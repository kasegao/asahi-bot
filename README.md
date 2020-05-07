# asahi-bot
A bot patrols the admissions page of the Graduate School of Information Science and Technology, the University of Tokyo and notifies you of updates via Slack.

## Requirement
If you don't have an AWS account, you'll need to create an account.

## Install
Prepare a Slack Integration, a S3 Bucket and a Lambda Function.

Create `config/asahi.ini` and describe as follows.

```ini
[slack]
webhook_url = https://hooks.slack.com/services/XXXXXXXX

[s3]
bucket_name = hoge
file_s3 = fuga
```

Run `build.sh` to create `lambda_function.zip`
```shell
$ bash build.sh
```

Upload `lambda_function.zip` to Lambda and set as follows.
- Runtime: Python 3.7
- Handler: `bot.lambda_handler`


Set CloudWatch Events to run periodically.
If you want to run it every 30 minutes, see below.

```cron
cron(0/30 * * * ? *)
```

Finally, run the Test Event only once to initialize it.
The event configuration file can be something like the following.

```json
{
  "key1": "value1"
}
```