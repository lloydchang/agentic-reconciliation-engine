## Using This as a Reference Implementation

You can include this repository in your own project as a `git submodule` — this keeps the commit histories separate, which is important for license clarity (see [Why not `git subtree`?](#why-not-git-subtree) below).

### Steps

1. [Create a new repository](https://github.com/new) and copy your `repository-name`

2. Run the following commands:

```bash
git init
git submodule add https://github.com/lloydchang/gitops-infra-control-plane
git commit -m "first commit"
git branch -M main
git remote add origin git@github.com:[your-github-username]/[repository-name].git
git push -u origin main
```

> **Note:** The commands above use SSH. If you haven't set up SSH keys, replace the `git remote add origin` line with the HTTPS URL shown in your new repository's setup page.

For more information on `git submodule`, see:
- [Git Tools - Submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [GitHub Docs - Creating a new repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)

### Why not `git subtree`?

`git subtree` merges the subproject's commit history directly into your repository's history, making it difficult to keep this project's [AGPLv3 `LICENSE`](./LICENSE) separate from your own repository's license.

Using `git submodule` keeps the two repositories — and their licenses — cleanly separated.
