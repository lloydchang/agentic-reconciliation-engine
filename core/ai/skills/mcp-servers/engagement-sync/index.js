#!/usr/bin/env node

/**
 * Engagement Sync MCP Server
 * 
 * This MCP server provides stakeholder engagement synchronization:
 * - Meeting scheduling and coordination
 * - Stakeholder communication tracking
 * - Decision dissemination
 * - Feedback collection and analysis
 * - Engagement metrics and reporting
 * - Cross-platform synchronization
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} = require('@modelcontextprotocol/sdk/types.js');

// External APIs and utilities
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

class EngagementSyncServer {
  constructor() {
    this.server = new Server(
      {
        name: 'engagement-sync-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.setupErrorHandling();
    
    // In-memory engagement store (in production, use a proper database)
    this.engagementStore = new Map();
    this.stakeholderStore = new Map();
    this.meetingStore = new Map();
  }

  setupErrorHandling() {
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'schedule_meeting',
          description: 'Schedule and coordinate meetings with stakeholders',
          inputSchema: {
            type: 'object',
            properties: {
              title: {
                type: 'string',
                description: 'Meeting title'
              },
              description: {
                type: 'string',
                description: 'Meeting description and agenda'
              },
              participants: {
                type: 'array',
                items: { type: 'string' },
                description: 'List of participant emails or IDs'
              },
              duration: {
                type: 'string',
                default: '1h',
                description: 'Meeting duration (e.g., 30m, 1h, 2h)'
              },
              preferred_times: {
                type: 'array',
                items: { type: 'string' },
                description: 'Preferred time slots (ISO 8601 format)'
              },
              meeting_type: {
                type: 'string',
                enum: ['standup', 'planning', 'retrospective', 'review', 'decision', 'stakeholder_update'],
                description: 'Type of meeting'
              },
              auto_send_invites: {
                type: 'boolean',
                default: true,
                description: 'Automatically send calendar invites'
              },
              calendar_integration: {
                type: 'string',
                enum: ['google', 'outlook', 'slack', 'teams'],
                description: 'Calendar integration to use'
              }
            }
          }
        },
        {
          name: 'track_communication',
          description: 'Track and analyze stakeholder communications',
          inputSchema: {
            type: 'object',
            properties: {
              communication_id: {
                type: 'string',
                description: 'Unique communication identifier'
              },
              type: {
                type: 'string',
                enum: ['email', 'slack', 'teams', 'meeting', 'document', 'announcement'],
                description: 'Communication type'
              },
              participants: {
                type: 'array',
                items: { type: 'string' },
                description: 'Participants involved'
              },
              content: {
                type: 'string',
                description: 'Communication content summary'
              },
              sentiment: {
                type: 'string',
                enum: ['positive', 'neutral', 'negative', 'mixed'],
                description: 'Communication sentiment'
              },
              engagement_level: {
                type: 'string',
                enum: ['high', 'medium', 'low'],
                description: 'Engagement level of participants'
              },
              follow_up_required: {
                type: 'boolean',
                default: false,
                description: 'Whether follow-up is required'
              }
            }
          }
        },
        {
          name: 'disseminate_decision',
          description: 'Disseminate decisions to relevant stakeholders',
          inputSchema: {
            type: 'object',
            properties: {
              decision_id: {
                type: 'string',
                description: 'Decision identifier'
              },
              decision_title: {
                type: 'string',
                description: 'Decision title'
              },
              decision_summary: {
                type: 'string',
                description: 'Decision summary and rationale'
              },
              stakeholders: {
                type: 'array',
                items: { type: 'string' },
                description: 'Stakeholders to notify'
              },
              channels: {
                type: 'array',
                items: { type: 'string' },
                enum: ['email', 'slack', 'teams', 'document', 'announcement'],
                description: 'Communication channels to use'
              },
              priority: {
                type: 'string',
                enum: ['low', 'medium', 'high', 'urgent'],
                default: 'medium',
                description: 'Communication priority'
              },
              acknowledgement_required: {
                type: 'boolean',
                default: false,
                description: 'Require acknowledgement from stakeholders'
              }
            }
          }
        },
        {
          name: 'collect_feedback',
          description: 'Collect and analyze feedback from stakeholders',
          inputSchema: {
            type: 'object',
            properties: {
              feedback_id: {
                type: 'string',
                description: 'Feedback collection identifier'
              },
              topic: {
                type: 'string',
                description: 'Topic for feedback collection'
              },
              stakeholders: {
                type: 'array',
                items: { type: 'string' },
                description: 'Stakeholders to collect feedback from'
              },
              feedback_type: {
                type: 'string',
                enum: ['survey', 'poll', 'interview', 'review', 'suggestion'],
                description: 'Type of feedback collection'
              },
              questions: {
                type: 'array',
                items: { type: 'string' },
                description: 'Feedback questions or prompts'
              },
              deadline: {
                type: 'string',
                description: 'Feedback collection deadline (ISO 8601 format)'
              },
              anonymous: {
                type: 'boolean',
                default: false,
                description: 'Allow anonymous feedback'
              }
            }
          }
        },
        {
          name: 'generate_engagement_report',
          description: 'Generate comprehensive engagement metrics and reports',
          inputSchema: {
            type: 'object',
            properties: {
              report_type: {
                type: 'string',
                enum: ['weekly', 'monthly', 'quarterly', 'project', 'stakeholder'],
                description: 'Type of engagement report'
              },
              time_period: {
                type: 'string',
                description: 'Time period for the report (e.g., 2024-01, Q1-2024)'
              },
              stakeholders: {
                type: 'array',
                items: { type: 'string' },
                description: 'Specific stakeholders to include (optional)'
              },
              include_metrics: {
                type: 'array',
                items: { type: 'string' },
                description: 'Metrics to include in report',
                default: ['participation', 'sentiment', 'response_time', 'engagement_score']
              },
              format: {
                type: 'string',
                enum: ['JSON', 'PDF', 'HTML'],
                default: 'JSON',
                description: 'Report output format'
              }
            }
          }
        },
        {
          name: 'sync_platforms',
          description: 'Synchronize engagement data across platforms',
          inputSchema: {
            type: 'object',
            properties: {
              platforms: {
                type: 'array',
                items: { type: 'string' },
                enum: ['slack', 'teams', 'email', 'calendar', 'jira', 'confluence'],
                description: 'Platforms to synchronize'
              },
              sync_type: {
                type: 'string',
                enum: ['full_sync', 'incremental', 'meeting_sync', 'decision_sync'],
                default: 'incremental',
                description: 'Type of synchronization'
              },
              time_range: {
                type: 'string',
                description: 'Time range for incremental sync (e.g., 24h, 7d, 30d)'
              },
              conflict_resolution: {
                type: 'string',
                enum: ['latest_wins', 'manual_review', 'merge'],
                default: 'latest_wins',
                description: 'How to resolve conflicts during sync'
              }
            }
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'schedule_meeting':
            return await this.scheduleMeeting(args);
          case 'track_communication':
            return await this.trackCommunication(args);
          case 'disseminate_decision':
            return await this.disseminateDecision(args);
          case 'collect_feedback':
            return await this.collectFeedback(args);
          case 'generate_engagement_report':
            return await this.generateEngagementReport(args);
          case 'sync_platforms':
            return await this.syncPlatforms(args);
          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
        }
      } catch (error) {
        console.error(`Error in ${name}:`, error);
        throw new McpError(ErrorCode.InternalError, `Tool execution failed: ${error.message}`);
      }
    });
  }

  async scheduleMeeting(args) {
    const { 
      title, 
      description, 
      participants, 
      duration = '1h', 
      preferred_times, 
      meeting_type,
      auto_send_invites = true,
      calendar_integration
    } = args;
    
    try {
      const meeting_id = uuidv4();
      
      // Find optimal time slot
      const optimal_time = await this.findOptimalMeetingTime(participants, preferred_times, duration);
      
      // Create meeting record
      const meeting = {
        id: meeting_id,
        title,
        description,
        participants,
        duration,
        scheduled_time: optimal_time,
        meeting_type,
        status: 'scheduled',
        created_at: new Date().toISOString(),
        calendar_integration,
        invites_sent: false
      };
      
      // Store meeting
      this.meetingStore.set(meeting_id, meeting);
      
      // Send calendar invites if requested
      if (auto_send_invites && calendar_integration) {
        const invite_result = await this.sendCalendarInvites(meeting, calendar_integration);
        meeting.invites_sent = true;
        meeting.invite_results = invite_result;
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'meeting_scheduled',
              meeting,
              message: `Meeting scheduled successfully for ${optimal_time}`
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Meeting scheduling failed: ${error.message}`);
    }
  }

  async trackCommunication(args) {
    const { 
      communication_id, 
      type, 
      participants, 
      content, 
      sentiment, 
      engagement_level,
      follow_up_required = false
    } = args;
    
    try {
      const communication = {
        id: communication_id || uuidv4(),
        type,
        participants,
        content,
        sentiment,
        engagement_level,
        follow_up_required,
        timestamp: new Date().toISOString(),
        metadata: {
          participant_count: participants.length,
          content_length: content.length
        }
      };
      
      // Store communication
      this.engagementStore.set(communication.id, communication);
      
      // Update participant engagement metrics
      await this.updateParticipantEngagement(participants, communication);
      
      // Generate insights
      const insights = await this.generateCommunicationInsights(communication);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'communication_tracked',
              communication,
              insights
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Communication tracking failed: ${error.message}`);
    }
  }

  async disseminateDecision(args) {
    const { 
      decision_id, 
      decision_title, 
      decision_summary, 
      stakeholders, 
      channels,
      priority = 'medium',
      acknowledgement_required = false
    } = args;
    
    try {
      const dissemination = {
        id: uuidv4(),
        decision_id,
        decision_title,
        decision_summary,
        stakeholders,
        channels,
        priority,
        acknowledgement_required,
        created_at: new Date().toISOString(),
        status: 'pending',
        delivery_results: []
      };
      
      // Send decision through each channel
      for (const channel of channels) {
        try {
          const result = await this.sendDecisionThroughChannel(dissemination, channel);
          dissemination.delivery_results.push({
            channel,
            success: true,
            result,
            sent_at: new Date().toISOString()
          });
        } catch (error) {
          dissemination.delivery_results.push({
            channel,
            success: false,
            error: error.message,
            sent_at: new Date().toISOString()
          });
        }
      }
      
      // Update status based on delivery results
      const allSuccessful = dissemination.delivery_results.every(r => r.success);
      dissemination.status = allSuccessful ? 'sent' : 'partial_failure';
      
      // Store dissemination record
      this.engagementStore.set(dissemination.id, dissemination);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'decision_disseminated',
              dissemination,
              message: `Decision disseminated to ${stakeholders.length} stakeholders via ${channels.length} channels`
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Decision dissemination failed: ${error.message}`);
    }
  }

  async collectFeedback(args) {
    const { 
      feedback_id, 
      topic, 
      stakeholders, 
      feedback_type, 
      questions, 
      deadline,
      anonymous = false
    } = args;
    
    try {
      const feedback_collection = {
        id: feedback_id || uuidv4(),
        topic,
        stakeholders,
        feedback_type,
        questions,
        deadline,
        anonymous,
        created_at: new Date().toISOString(),
        status: 'active',
        responses: [],
        reminders_sent: 0
      };
      
      // Store feedback collection
      this.engagementStore.set(feedback_collection.id, feedback_collection);
      
      // Send feedback requests
      const request_results = await this.sendFeedbackRequests(feedback_collection);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'feedback_collection_started',
              feedback_collection,
              request_results,
              message: `Feedback collection started for ${stakeholders.length} stakeholders`
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Feedback collection failed: ${error.message}`);
    }
  }

  async generateEngagementReport(args) {
    const { 
      report_type, 
      time_period, 
      stakeholders, 
      include_metrics = ['participation', 'sentiment', 'response_time', 'engagement_score'],
      format = 'JSON'
    } = args;
    
    try {
      const report = {
        id: uuidv4(),
        type: report_type,
        time_period,
        stakeholders,
        metrics: include_metrics,
        format,
        generated_at: new Date().toISOString(),
        data: {}
      };
      
      // Generate metrics based on requested types
      for (const metric of include_metrics) {
        switch (metric) {
          case 'participation':
            report.data.participation = await this.calculateParticipationMetrics(time_period, stakeholders);
            break;
          case 'sentiment':
            report.data.sentiment = await this.calculateSentimentMetrics(time_period, stakeholders);
            break;
          case 'response_time':
            report.data.response_time = await this.calculateResponseTimeMetrics(time_period, stakeholders);
            break;
          case 'engagement_score':
            report.data.engagement_score = await this.calculateEngagementScore(time_period, stakeholders);
            break;
        }
      }
      
      // Generate summary and recommendations
      report.summary = await this.generateEngagementSummary(report.data);
      report.recommendations = await this.generateEngagementRecommendations(report.data);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'engagement_report',
              report
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Engagement report generation failed: ${error.message}`);
    }
  }

  async syncPlatforms(args) {
    const { 
      platforms, 
      sync_type = 'incremental', 
      time_range, 
      conflict_resolution = 'latest_wins'
    } = args;
    
    try {
      const sync_result = {
        id: uuidv4(),
        platforms,
        sync_type,
        time_range,
        conflict_resolution,
        started_at: new Date().toISOString(),
        results: {},
        conflicts: [],
        summary: {}
      };
      
      // Perform sync for each platform
      for (const platform of platforms) {
        try {
          const platform_result = await this.syncPlatform(platform, sync_type, time_range, conflict_resolution);
          sync_result.results[platform] = {
            success: true,
            ...platform_result
          };
        } catch (error) {
          sync_result.results[platform] = {
            success: false,
            error: error.message
          };
        }
      }
      
      // Generate sync summary
      sync_result.summary = {
        total_platforms: platforms.length,
        successful_syncs: Object.values(sync_result.results).filter(r => r.success).length,
        failed_syncs: Object.values(sync_result.results).filter(r => !r.success).length,
        total_conflicts: sync_result.conflicts.length,
        completed_at: new Date().toISOString()
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'platform_sync_completed',
              sync_result
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Platform synchronization failed: ${error.message}`);
    }
  }

  // Helper methods
  async findOptimalMeetingTime(participants, preferredTimes, duration) {
    // Mock implementation - in production, integrate with actual calendar APIs
    if (preferredTimes && preferredTimes.length > 0) {
      return preferredTimes[0];
    }
    
    // Default to next business day at 10 AM
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(10, 0, 0, 0);
    
    return tomorrow.toISOString();
  }

  async sendCalendarInvites(meeting, calendarIntegration) {
    // Mock calendar integration
    return {
      integration: calendarIntegration,
      invites_sent: meeting.participants.length,
      calendar_event_id: uuidv4(),
      success: true
    };
  }

  async updateParticipantEngagement(participants, communication) {
    // Update engagement metrics for each participant
    for (const participant of participants) {
      if (!this.stakeholderStore.has(participant)) {
        this.stakeholderStore.set(participant, {
          id: participant,
          communications: [],
          engagement_score: 0,
          last_activity: new Date().toISOString()
        });
      }
      
      const stakeholder = this.stakeholderStore.get(participant);
      stakeholder.communications.push({
        communication_id: communication.id,
        type: communication.type,
        timestamp: communication.timestamp,
        engagement_level: communication.engagement_level
      });
      
      stakeholder.last_activity = communication.timestamp;
      
      // Recalculate engagement score
      stakeholder.engagement_score = this.calculateEngagementScoreForStakeholder(stakeholder);
    }
  }

  calculateEngagementScoreForStakeholder(stakeholder) {
    // Simple engagement score calculation
    const recentCommunications = stakeholder.communications.filter(
      c => new Date(c.timestamp) > new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) // Last 30 days
    );
    
    if (recentCommunications.length === 0) return 0;
    
    const engagementWeights = { high: 3, medium: 2, low: 1 };
    const totalScore = recentCommunications.reduce((sum, comm) => {
      return sum + (engagementWeights[comm.engagement_level] || 1);
    }, 0);
    
    return Math.min(100, (totalScore / recentCommunications.length) * 20);
  }

  async generateCommunicationInsights(communication) {
    // Generate insights from communication data
    const insights = [];
    
    // Participation insight
    if (communication.participants.length > 5) {
      insights.push({
        type: 'high_participation',
        message: `High participation with ${communication.participants.length} participants`,
        confidence: 0.8
      });
    }
    
    // Sentiment insight
    if (communication.sentiment === 'negative') {
      insights.push({
        type: 'negative_sentiment',
        message: 'Negative sentiment detected - may require follow-up',
        confidence: 0.7
      });
    }
    
    // Engagement insight
    if (communication.engagement_level === 'low') {
      insights.push({
        type: 'low_engagement',
        message: 'Low engagement level - consider different approach',
        confidence: 0.6
      });
    }
    
    return insights;
  }

  async sendDecisionThroughChannel(dissemination, channel) {
    // Mock channel-specific sending
    switch (channel) {
      case 'email':
        return await this.sendEmailDecision(dissemination);
      case 'slack':
        return await this.sendSlackDecision(dissemination);
      case 'teams':
        return await this.sendTeamsDecision(dissemination);
      case 'document':
        return await this.createDecisionDocument(dissemination);
      default:
        throw new Error(`Unsupported channel: ${channel}`);
    }
  }

  async sendEmailDecision(dissemination) {
    // Mock email sending
    return {
      channel: 'email',
      recipients: dissemination.stakeholders.length,
      message_id: uuidv4(),
      sent_at: new Date().toISOString()
    };
  }

  async sendSlackDecision(dissemination) {
    // Mock Slack sending
    return {
      channel: 'slack',
      channels_notified: 1,
      message_id: uuidv4(),
      sent_at: new Date().toISOString()
    };
  }

  async sendTeamsDecision(dissemination) {
    // Mock Teams sending
    return {
      channel: 'teams',
      teams_notified: 1,
      message_id: uuidv4(),
      sent_at: new Date().toISOString()
    };
  }

  async createDecisionDocument(dissemination) {
    // Mock document creation
    return {
      channel: 'document',
      document_id: uuidv4(),
      document_url: `https://docs.company.com/decisions/${dissemination.decision_id}`,
      created_at: new Date().toISOString()
    };
  }

  async sendFeedbackRequests(feedbackCollection) {
    // Mock feedback request sending
    const results = {
      requests_sent: feedbackCollection.stakeholders.length,
      delivery_method: feedbackCollection.feedback_type,
      estimated_response_rate: 0.7,
      sent_at: new Date().toISOString()
    };
    
    return results;
  }

  async calculateParticipationMetrics(timePeriod, stakeholders) {
    // Mock participation metrics calculation
    return {
      total_participants: stakeholders ? stakeholders.length : 10,
      active_participants: 8,
      participation_rate: 0.8,
      meetings_attended: 15,
      communications_sent: 45
    };
  }

  async calculateSentimentMetrics(timePeriod, stakeholders) {
    // Mock sentiment metrics calculation
    return {
      overall_sentiment: 'positive',
      sentiment_distribution: {
        positive: 0.6,
        neutral: 0.3,
        negative: 0.1
      },
      sentiment_trend: 'improving',
      key_sentiment_drivers: ['project_progress', 'team_collaboration']
    };
  }

  async calculateResponseTimeMetrics(timePeriod, stakeholders) {
    // Mock response time metrics calculation
    return {
      average_response_time: '2.5 hours',
      median_response_time: '1.8 hours',
      response_rate: 0.85,
      fastest_response: '15 minutes',
      slowest_response: '24 hours'
    };
  }

  async calculateEngagementScore(timePeriod, stakeholders) {
    // Mock engagement score calculation
    return {
      overall_score: 78,
      score_breakdown: {
        participation: 85,
        communication: 72,
        responsiveness: 80,
        collaboration: 75
      },
      trend: 'improving',
      benchmark_comparison: 'above_average'
    };
  }

  async generateEngagementSummary(data) {
    // Generate executive summary
    return {
      overall_health: 'good',
      key_highlights: [
        'High participation rate across all stakeholders',
        'Positive sentiment trend detected',
        'Response times within acceptable range'
      ],
      areas_for_improvement: [
        'Increase engagement in specific project areas',
        'Improve communication consistency'
      ],
      next_steps: [
        'Schedule follow-up meetings with low-engagement stakeholders',
        'Implement automated feedback collection'
      ]
    };
  }

  async generateEngagementRecommendations(data) {
    // Generate actionable recommendations
    const recommendations = [];
    
    if (data.participation?.participation_rate < 0.7) {
      recommendations.push({
        priority: 'high',
        category: 'participation',
        description: 'Increase stakeholder participation through more inclusive meeting scheduling',
        expected_impact: '20% increase in participation rate'
      });
    }
    
    if (data.sentiment?.overall_sentiment === 'negative') {
      recommendations.push({
        priority: 'urgent',
        category: 'sentiment',
        description: 'Address negative sentiment through targeted communication and issue resolution',
        expected_impact: 'Improved team morale and collaboration'
      });
    }
    
    if (data.response_time?.average_response_time > '4 hours') {
      recommendations.push({
        priority: 'medium',
        category: 'responsiveness',
        description: 'Implement response time SLAs and automated reminders',
        expected_impact: '50% reduction in average response time'
      });
    }
    
    return recommendations;
  }

  async syncPlatform(platform, syncType, timeRange, conflictResolution) {
    // Mock platform synchronization
    return {
      platform,
      sync_type: syncType,
      time_range: timeRange,
      records_synced: 150,
      conflicts_resolved: 3,
      sync_duration: '2.5 minutes',
      last_sync: new Date().toISOString()
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Engagement Sync MCP server running on stdio');
  }
}

// Run the server
if (require.main === module) {
  const server = new EngagementSyncServer();
  server.run().catch(console.error);
}

module.exports = EngagementSyncServer;
