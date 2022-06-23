# Start the MFA
        aws-mfa --duration 43200 --device arn:aws:iam::415102591172:mfa/majd.rezik.2

## mount also the MFA credentials
>        docker run -it -v $PWD:/opt/deployer \
        -v /Users/majdrezik/.aws/credentials:/root/.aws/credentials \
        -w /opt/deployer --entrypoint /bin/bash "devopslets/gs-cli-alb:latest_develop"

## then we activate the venv.
>       . /gsdeployer/bin/activate

## then we run the deployer with our deployer_settings.yml
>       PYTHONPATH=. deploy_vpc deploy --env staging --role majdPetclinic --bld 59 --branch main --flavor t2.medium --asg-size 2 --region us-west-2  --on-demand

## In order to see the logs:
less /var/log/cloud-init-output.log

Current Error:
                                                ERROR
---------->                                                                                      <----------
---------->     Failed to run module scripts-user (scripts in /var/lib/cloud/instance/scripts)   <----------
---------->                                                                                      <----------

NOTE:   This dir has only one file. (part-001)
        This file has my userData script that I provided to the deployer.

Solution:::

I deleted the extra line before shebang in the script!








(Without CLI MFA)
## First we pull the image from docker hub:
>       docker run -it -v $PWD:/opt/deployer -w /opt/deployer --entrypoint /bin/bash "devopslets/gs-cli-alb:latest_develop" 


PWD is the directory with the files.

(NOT ANYMORE)
## Export Credentials:
>       export AWS_ACCESS_KEY_ID="access"
>       export AWS_SECRET_ACCESS_KEY="secret"




### Template

>       PYTHONPATH=. deploy_vpc deploy --env ${THE_ENV} --role %DEPL_role% --bld %DEP_BLD.number% --branch %DEP_BLD.branch% --flavor %INST_FLAVOR% --asg-size %ASG_SIZE% --region %AWS_REGION%  --ami-override %ami_override% --on-demand


### Carrot top ^
We use the carrot top ^ to specify the value of the given parameter from the CLI.
ie.     .../main/59/...
        .../^branch/^branchNumber/...