# Monthly Cost Assumptions

## Assumptions

| Assumption                                   |                 Value |
| -------------------------------------------- | --------------------: |
| Meetings per month                           |                    20 |
| Average meeting duration                     |            60 minutes |
| Estimated transcript size per meeting        |   12,000 input tokens |
| AI output budget per meeting                 |   2,000 output tokens |
| Monthly input token volume                   |        240,000 tokens |
| Monthly output token volume                  |         40,000 tokens |
| Recording retention                          |               30 days |
| Existing Google Workspace and Slack licenses | Assumed already owned |

The 2,000-token output budget covers the executive summary, three objectives, three action items, next steps, evidence references, and risks. It is intentionally higher than the expected final slide content so the system has room to return valid structured JSON.

## Official OpenAI Pricing

* GPT-4.1: [OpenAI model page](https://developers.openai.com/api/docs/models/gpt-4.1)
* GPT-5.5: [OpenAI model page](https://developers.openai.com/api/docs/models/gpt-5.5)
* Transcription and all API pricing: [OpenAI pricing page](https://developers.openai.com/api/docs/pricing)

| Model   | Input per 1M tokens | Output per 1M tokens |
| ------- | ------------------: | -------------------: |
| GPT-4.1 |               $2.00 |                $8.00 |
| GPT-5.5 |               $5.00 |               $30.00 |

## Scenario 1: Existing Transcript

This scenario applies when Google Meet or Zoom already provides a usable transcript.

### Cost per meeting

| Cost item           | GPT-4.1 | GPT-5.5 |
| ------------------- | ------: | ------: |
| 12,000 input tokens |  $0.024 |  $0.060 |
| 2,000 output tokens |  $0.016 |  $0.060 |
| Total per meeting   |  $0.040 |  $0.120 |

### Monthly cost for 20 meetings

| Cost item                                            |              GPT-4.1 |              GPT-5.5 |
| ---------------------------------------------------- | -------------------: | -------------------: |
| LLM input                                            |                $0.48 |                $1.20 |
| LLM output                                           |                $0.32 |                $1.20 |
| Total LLM cost                                       |                $0.80 |                $2.40 |
| Estimated Cloud Run, Pub/Sub, Firestore, and storage |       $0.50 to $2.00 |       $0.50 to $2.00 |
| Estimated monthly total                              | about $1.30 to $2.80 | about $2.90 to $4.40 |

## Scenario 2: One-Hour Recording Without Transcript

This scenario applies when the workflow must transcribe a 60-minute recording before generating the summary.

Transcription assumption:

```text
20 meetings x 60 minutes x $0.006 per minute = $7.20 per month
```

| Cost item                                            |               GPT-4.1 |                GPT-5.5 |
| ---------------------------------------------------- | --------------------: | ---------------------: |
| Transcription for 20 one-hour meetings               |                 $7.20 |                  $7.20 |
| LLM processing for 20 meetings                       |                 $0.80 |                  $2.40 |
| Estimated Cloud Run, Pub/Sub, Firestore, and storage |        $0.50 to $2.00 |         $0.50 to $2.00 |
| Estimated monthly total                              | about $8.50 to $10.00 | about $10.10 to $11.60 |

## Revision Allowance

Assume that 25% of meetings require one content revision.

That equals five revision requests per month.

| Model   | Extra monthly LLM cost for five revisions |
| ------- | ----------------------------------------: |
| GPT-4.1 |                               about $0.20 |
| GPT-5.5 |                               about $0.60 |

This assumes each revision again uses 12,000 input tokens and 2,000 output tokens.

## Recommendation

Use GPT-4.1 as the normal extraction model. It is more than adequate for structured meeting summaries and keeps costs extremely low.

Use GPT-5.5 only for selected situations:

* High-stakes executive meetings
* Complex or ambiguous meetings
* Revision requests requiring stronger reasoning
* Meetings where the first extraction fails validation or needs deeper synthesis

The main variable cost is transcription, not LLM summarization. When Google Meet or Zoom already provides a transcript, the workflow becomes very inexpensive.
