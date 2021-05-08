import boto3
import xmltodict

MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'

mturk = boto3.client('mturk',
   aws_access_key_id = "AKIAS6Q65BL5SAEDVUNK",
   aws_secret_access_key = "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",
   region_name='us-east-1',
   endpoint_url = MTURK_SANDBOX
)

hit_id = '3UZUVSO3P9IC8ES6KQM0K9YEEEFMEM'

worker_results = mturk.list_assignments_for_hit(HITId=hit_id, AssignmentStatuses=['Submitted'])
