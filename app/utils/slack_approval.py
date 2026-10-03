# app/utils/slack_approval.py
import requests
import json
from ..utils.config import SLACK_WEBHOOK_URL

class SlackApprovalSystem:
    def __init__(self):
        self.webhook_url = SLACK_WEBHOOK_URL
    
    def send_approval_request(self, content_type, content, lead_name, post_url, task_id):
        """Send message to Slack for human approval"""
        
        if content_type == "comment":
            action_text = "comment on post"
            approve_action = "approve_comment"
            deny_action = "deny_comment"
        else:  # email or dm
            action_text = "send message to lead"
            approve_action = "approve_message"
            deny_action = "deny_message"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🤖 Approval Required: {action_type.title()}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Lead:* {lead_name}\n*Post:* {post_url}\n*Content:*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": content[:200] + "..." if len(content) > 200 else content
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Approve"
                        },
                        "style": "primary",
                        "value": json.dumps({
                            "task_id": task_id,
                            "action": approve_action,
                            "content": content
                        })
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ Deny"
                        },
                        "style": "danger",
                        "value": json.dumps({
                            "task_id": task_id,
                            "action": deny_action
                        })
                    }
                ]
            }
        ]
        
        payload = {"blocks": blocks}
        response = requests.post(self.webhook_url, json=payload)
        return response.status_code == 200