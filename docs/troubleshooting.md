# Troubleshooting

## Terraform locking
In case you have your deployment script interrupted, you may have the "Error: Error locking state: Error acquiring the state lock" message.
To disable Terraform locking, export the following variable. This has to be done once. After rerunning the deploy script, the lock will be released.

```shell
export ICL_TERRAFORM_DISABLE_LOCKING=1
```
