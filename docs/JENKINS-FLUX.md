# Jenkins + Flux

## Disclaimer

Note that this guide has not been updated since more than a year ago, it does not address Kubernetes 1.24 or above, and needs to be refreshed.

Expect this doc to either be archived soon, or to receive an overhaul.

## Overview

This guide explains how to configure Flux with Jenkins, with the core ideas of GitOps Principles in mind. Let Jenkins handle CI (Continuous Integration: image build and test, tagging and pushing), and let Flux handle CD (Continuous Deployment) by making use of the Image Update Automation feature.

## Declarative Artifacts

In traditional CI/CD systems like Jenkins, the CI infra is often made directly responsible for continuous delivery. Flux treats this arrangement as dangerous, and mitigates this risk by prescribing encapsulation of resources into declarative artifacts, and a strict boundary separating CI from CD.

Jenkins can be cumbersome, and CI builds are an imperative operation that can succeed or fail including sometimes for surprising reasons. Flux obviates any deploy-time link between Jenkins and production deployments, to fulfill the promises of increased reliability and repeatability with GitOps.

## Git Manifests

Flux requires YAML manifests to be kept in a git repository. Flux's Source Controller periodically reconciles the config repository where the cluster's YAML manifests are maintained.

Flux represents this as a GitRepository custom resource that points to a branch, tag, or specific commit.

## Image Repository

Jenkins is responsible for building and testing OCI images. Those images can be tested internally on Jenkins as part of the build, before pushing, or once deployed in a non-production cluster.

Jenkins workflows are often as varied and complex as a snowflake. Finer points of Jenkins image building are not in scope for this guide.

## Jenkins Builds OCI Images

While many companies use Jenkins for building Docker images, it isn't actually true that Jenkins builds Docker images. Docker builds OCI images, and Jenkins shells out to Docker.

Jenkins always uses some other tool to build OCI images. Docker may be the most common, but other tools like Porter, Buildpacks.io, Earthfile can also be used.

## Security Concerns

Using privileged pods and HostPath volumes for Docker access is dangerous. You should not do these things without understanding the risks. Don't run untrusted code near production clusters.

Dockershim was formally deprecated. You may want to use another tool to produce OCI images with Jenkins.

## Example Jenkinsfile

Adapt this Jenkinsfile for your project. It builds images for development and production, with proper tagging and testing.

```groovy
dockerRepoHost = 'docker.io'
dockerRepoUser = 'youruser'
dockerRepoProj = 'yourproject'
jenkinsDockerSecret = 'docker-registry-account'

pipeline {
  agent {
    kubernetes { yamlFile "jenkins/docker-pod.yaml" }
  }
  stages {
    stage('Build') {
      steps {
        container('docker') {
          script {
            gitCommit = env.GIT_COMMIT.substring(0,8)
            branchName = env.BRANCH_NAME
            unixTime = (new Date().time.intdiv(1000))
            developmentTag = "${branchName}-${gitCommit}-${unixTime}"
            developmentImage = "${dockerRepoUser}/${dockerRepoProj}:${developmentTag}"
          }
          sh "docker build -t ${developmentImage} ./"
        }
      }
    }
    stage('Dev') {
      parallel {
        stage('Push Development Tag') {
          when {
            not {
              buildingTag()
            }
          }
          steps {
            withCredentials([[$class: 'UsernamePasswordMultiBinding',
              credentialsId: jenkinsDockerSecret,
              usernameVariable: 'DOCKER_REPO_USER',
              passwordVariable: 'DOCKER_REPO_PASSWORD']]) {
              container('docker') {
                sh """\
                  docker login -u \$DOCKER_REPO_USER -p \$DOCKER_REPO_PASSWORD
                  docker push ${developmentImage}
                """.stripIndent()
              }
            }
          }
        }
        stage('Test') {
          agent {
            kubernetes {
              yaml """\
                apiVersion: v1
                kind: Pod
                spec:
                  containers:
                  - name: test
                    image: ${developmentImage}
                    imagePullPolicy: Never
                    securityContext:
                      runAsUser: 1000
                    command:
                    - cat
                    resources:
                      requests:
                        memory: 256Mi
                        cpu: 50m
                      limits:
                        memory: 1Gi
                        cpu: 1200m
                    tty: true
                """.stripIndent()
            }
          }
          options { skipDefaultCheckout(true) }
          steps {
            container('test') {
              sh (script: "/app/jenkins/run-tests.sh")
            }
          }
        }
      }
    }
    stage('Push Release Tag') {
      when {
        buildingTag()
      }
      steps {
        script {
          releaseTag = env.TAG_NAME
          releaseImage = "${dockerRepoUser}/${dockerRepoProj}:${releaseTag}"
        }
        container('docker') {
          withCredentials([[$class: 'UsernamePasswordMultiBinding',
            credentialsId: jenkinsDockerSecret,
            usernameVariable: 'DOCKER_REPO_USER',
            passwordVariable: 'DOCKER_REPO_PASSWORD']]) {
            sh """\
              docker login -u \$DOCKER_REPO_USER -p \$DOCKER_REPO_PASSWORD
              docker tag ${developmentImage} ${releaseImage}
              docker push ${releaseImage}
            """.stripIndent()
          }
        }
      }
    }
  }
}
```

## Instructions for Use

1. Fork the example repo from kingdonb/jenkins-example-workflow
2. Add this Jenkinsfile to your project repository
3. Configure a Multibranch Pipeline to trigger on branch/tag pushes
4. Set up Docker registry credentials in Jenkins

## Development vs Release Images

### Development Images

- Tagged with sortable format: `{branch}-{sha}-{timestamp}`
- Pushed on every commit to branches
- Can be deployed automatically by Flux for dev environments

### Release Images

- Tagged with SemVer from Git tags
- Only pushed after tests pass
- Deployed to production via Flux ImagePolicy

## Flux Integration

### ImagePolicy for Production

```yaml
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: app
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: app
  policy:
    semver:
      range: 1.0.x
```

### ImageUpdateAutomation

```yaml
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageUpdateAutomation
metadata:
  name: app
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: flux-system
  git:
    checkout:
      ref:
        branch: main
  update:
    path: ./clusters/production
    strategy: Setters
```

## Repository Integration

This Jenkins + Flux integration works seamlessly with the GitOps Infra Control Plane. The platform provides comprehensive CI/CD integration capabilities.

### Integration Benefits

- **Separation of Concerns**: CI (Jenkins) builds and tests, CD (Flux) deploys
- **Security**: No direct production cluster access from CI
- **Reliability**: Declarative GitOps deployments
- **Automation**: Image updates via Flux policies

## Alternatives to Docker

If running Docker in privileged mode is not acceptable:

- **Buildkit**: Use `kubectl build` for rootless builds
- **Kaniko**: Google tool for building images in containers
- **Buildpacks**: Cloud-native build framework
- **Earthfile**: Alternative to Dockerfile syntax

## Wrap Up

Jenkins handles CI (building and testing images), Flux handles CD (deploying via GitOps). This separation provides better security, reliability, and scalability compared to traditional CI/CD pipelines that handle both CI and CD.

By pushing image tags, Jenkins can update clusters using Flux's pull-based model. When a new image is pushed that meets the configured policy, Flux automatically deploys it.

This works without Jenkins having any access to production clusters, maintaining strict separation between CI and CD responsibilities.

Last modified 2023-07-11: Mark some use-cases doc in need of refresh (f35e7b4)
