#!/usr/bin/env node

/**
 * Consensus Feedback Loop - TypeScript/Node.js Implementation
 * Event-driven consensus-based agent orchestration for infrastructure optimization.
 * Leverages Node.js event loop and JavaScript async/await for non-blocking consensus operations.
 */

import { EventEmitter } from 'events';
import * as process from 'process';

// Data structures for consensus
interface ConsensusProposal {
  id: string;
  agentType: string;
  description: string;
  priority: number;
  timestamp: Date;
  votesRequired: number;
  approved: boolean;
}

interface ConsensusState {
  quorumSize: number;
  protocol: string;
  activeProposals: Map<string, ConsensusProposal>;
  lastUpdate?: Date;
}

// Agent interface
interface ConsensusAgent {
  localOptimization(state: ConsensusState): Promise<ConsensusProposal | null>;
  voteOnProposal(proposal: ConsensusProposal): Promise<boolean>;
  executeConsensus(proposal: ConsensusProposal, votes: boolean[]): Promise<void>;
}

// Cost optimizer agent implementation
class CostOptimizerAgent implements ConsensusAgent {
  constructor(private state: ConsensusState) {}

  async localOptimization(state: ConsensusState): Promise<ConsensusProposal | null> {
    // Simulate local optimization work
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Mock: Sometimes create a proposal (30% chance)
    if (Math.random() < 0.3) {
      return {
        id: `proposal-${Date.now()}`,
        agentType: 'cost-optimizer',
        description: 'Scale EKS node group from 3 to 5 nodes',
        priority: 2,
        timestamp: new Date(),
        votesRequired: this.state.quorumSize,
        approved: false
      };
    }

    return null;
  }

  async voteOnProposal(proposal: ConsensusProposal): Promise<boolean> {
    // Weighted voting based on agent type
    await new Promise(resolve => setTimeout(resolve, 100)); // Simulate voting deliberation

    if (proposal.agentType === 'cost-optimizer') {
      return true; // Cost optimizer always approves cost-related proposals
    }

    // For other proposals, approve with 80% confidence
    return Math.random() < 0.8;
  }

  async executeConsensus(proposal: ConsensusProposal, votes: boolean[]): Promise<void> {
    console.log(`Executing consensus proposal: ${proposal.description}`);

    // Simulate infrastructure change execution
    await new Promise(resolve => setTimeout(resolve, 500));

    console.log('Consensus change executed successfully');
  }
}

// Main consensus feedback loop
class ConsensusFeedbackLoop extends EventEmitter {
  private consensusState: ConsensusState;
  private agents: ConsensusAgent[];
  private feedbackInterval: number;
  private quorumSize: number;
  private running: boolean = true;

  constructor() {
    super();

    // Read environment variables
    this.consensusState = {
      quorumSize: parseInt(process.env.AGENT_QUORUM || '3'),
      protocol: process.env.CONSENSUS_PROTOCOL || 'raft',
      activeProposals: new Map()
    };

    this.feedbackInterval = parseInt((process.env.FEEDBACK_INTERVAL || '30s').replace('s', ''));
    this.quorumSize = this.consensusState.quorumSize;

    // Initialize agents
    this.agents = [
      new CostOptimizerAgent(this.consensusState)
      // Add more agent types as needed
    ];

    // Setup signal handling for graceful shutdown
    process.on('SIGTERM', () => {
      console.log('Received SIGTERM, shutting down gracefully...');
      this.running = false;
    });

    process.on('SIGINT', () => {
      console.log('Received SIGINT, shutting down gracefully...');
      this.running = false;
    });
  }

  async runFeedbackLoop(): Promise<void> {
    console.log('Starting TypeScript consensus feedback loop');

    while (this.running) {
      try {
        // Phase 1: Local optimization (30 seconds)
        await this.runLocalOptimizationPhase();

        // Phase 2: Consensus proposal submission
        await this.runConsensusProposalPhase();

        // Phase 3: Vote collection
        await this.runVoteCollectionPhase();

        // Phase 4: Consensus execution
        await this.runConsensusExecutionPhase();

        // Wait for next iteration
        await new Promise(resolve => setTimeout(resolve, (60 - this.feedbackInterval) * 1000));
      } catch (error) {
        console.error(`Error in feedback loop iteration: ${(error as Error).message}`);
        await new Promise(resolve => setTimeout(resolve, 10000));
      }
    }
  }

  private async runLocalOptimizationPhase(): Promise<void> {
    console.log('Starting local optimization phase');

    try {
      // Run local optimization with timeout
      const optimizationTasks = this.agents.map(agent =>
        this.withTimeout(agent.localOptimization(this.consensusState), this.feedbackInterval * 1000)
      );

      const optimizationResults = await Promise.allSettled(optimizationTasks);

      for (const result of optimizationResults) {
        if (result.status === 'fulfilled' && result.value) {
          this.consensusState.activeProposals.set(result.value.id, result.value);
          console.log(`Created consensus proposal: ${result.value.id}`);
        }
      }
    } catch (error) {
      console.error(`Local optimization failed: ${(error as Error).message}`);
    }
  }

  private async runConsensusProposalPhase(): Promise<void> {
    if (this.consensusState.activeProposals.size === 0) {
      return;
    }

    for (const [proposalId, proposal] of this.consensusState.activeProposals) {
      try {
        // Submit to consensus protocol (simulated)
        await this.submitToConsensus(proposal);
        console.log(`Submitted proposal ${proposalId} to consensus`);
      } catch (error) {
        console.error(`Failed to submit proposal ${proposalId}: ${(error as Error).message}`);
      }
    }
  }

  private async runVoteCollectionPhase(): Promise<void> {
    for (const [proposalId, proposal] of this.consensusState.activeProposals) {
      try {
        const votes = await this.collectVotes(proposal);

        if (votes.filter(v => v).length >= proposal.votesRequired) {
          proposal.approved = true;
          console.log(`Proposal ${proposalId} reached quorum`);
        } else if (votes.length > 0) {
          console.log(`Proposal ${proposalId} has ${votes.filter(v => v).length} votes`);
        }
      } catch (error) {
        console.error(`Failed to collect votes for proposal ${proposalId}: ${(error as Error).message}`);
      }
    }
  }

  private async runConsensusExecutionPhase(): Promise<void> {
    for (const [proposalId, proposal] of this.consensusState.activeProposals) {
      if (proposal.approved) {
        try {
          // Collect final votes for execution
          const finalVotes = await this.collectVotes(proposal);
          await this.agents[0].executeConsensus(proposal, finalVotes);

          this.consensusState.activeProposals.delete(proposalId);
          console.log(`Executed approved proposal: ${proposalId}`);
        } catch (error) {
          console.error(`Failed to execute proposal ${proposalId}: ${(error as Error).message}`);
        }
      }
    }
  }

  private async submitToConsensus(proposal: ConsensusProposal): Promise<void> {
    // Simulate consensus protocol submission
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  private async collectVotes(proposal: ConsensusProposal): Promise<boolean[]> {
    // Simulate vote collection from agents
    const votes: boolean[] = [];

    for (const agent of this.agents) {
      try {
        const vote = await agent.voteOnProposal(proposal);
        votes.push(vote);
      } catch (error) {
        console.error(`Agent voting failed: ${(error as Error).message}`);
        votes.push(false); // Default to false on error
      }
    }

    return votes;
  }

  private async withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Operation timed out'));
      }, timeoutMs);

      promise
        .then(resolve)
        .catch(reject)
        .finally(() => clearTimeout(timeout));
    });
  }
}

// Main execution
async function main() {
  const loop = new ConsensusFeedbackLoop();

  try {
    await loop.runFeedbackLoop();
  } catch (error) {
    console.error(`Consensus feedback loop failed: ${(error as Error).message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

export { ConsensusFeedbackLoop, ConsensusProposal, ConsensusState, ConsensusAgent };
