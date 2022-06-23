from aws_deploy.deploy import AbcDeploySettings
from aws_deploy.deploy import settings
from pprint import pformat

import os
import yaml
import boto3
import logging


"""
This is a reference implementation for the configuration deployment settings
"""

DEFAULT_FLAVOR = 'm5.large'
AUTOSPOTTING_TAG = 'spot-enabled'
ENVS = {
    'staging': 'vpc-08a4e3ef6bd774cab',
}


class SampleDeploySettings(AbcDeploySettings):
    def __init__(self, *args, **kwargs):
        super(SampleDeploySettings, self).__init__(*args, **kwargs)  # role=role, env=env)

        print("kwargs\n%s\n%s\n--" % (args, kwargs))

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(os.getenv('LOG_LEVEL', logging.INFO))

        yaml_settings = yaml.load(open('./deploy_settings.yml'),Loader=yaml.FullLoader)
        self.role_defs = yaml_settings.get('roles')
        self.key_names = yaml_settings.get('general').get('key_names')
        self.vpcs = yaml_settings.get('general').get('vpcs')

    def create_aws_connections(self):
        # TODO - Change hardcoded region
        region = settings.context['region']
        # region = 'us-west-2'
        if not hasattr(self, 'ssn'):
            self.ssn = boto3.session.Session(region_name=region, profile_name='default')
            self.ec2_conn = self.ssn.client('ec2')
            self.asg_conn = self.ssn.client('autoscaling')
            self.cw_conn = self.ssn.client('cloudwatch')
            self.logger.info("created aws connections ")
        else:
            self.logger.info("aws connections already exist")

    def asg_termination_flow(self):
        return self.role_def().get('termination_flow', {'type': 'delay', 'value': 30})

    def prod_key(self):
        """ used to customize the prod_key"""
        return 'production'

    def role_def(self):
        role = self.role_defs[self.role]
        if settings.context['ami_override'] is not None:
            role['ami_id'] = settings.context['ami_override']
        return role

    def is_cluster_ready(self, cluster_size, current_live_instances):
        assert type(cluster_size) == int, "type(cluster_size) is not int:  %s" % type(cluster_size)
        assert type(current_live_instances) == int
        return current_live_instances >= cluster_size

    def cluster_size(self):
        """ get the cluster size"""
        if self.prod_key().lower() == self.env.lower():
            return self.role_def()['production_size']
        else:
            return 1

    def get_vpc_id(self):
        """ not mandatory, raise if used"""
        # import boto
        # vpc_conn = boto.connect_vpc()#settings.context.get('region'))
        # ?vpcs = vpc_conn.get_all_vpcs(filters={'tag:env': 'stg'})
        # print ">>>>. %s: %s"%(settings.context.get('region'),vpcs)
        # return self.vpc_id
        return self.vpcs[self.env.lower()]

    def instance_flavor(self):
        if settings.context.get('flavor') is not None:
            return settings.context.get('flavor')
        return self.role_defs[self.role].get('flavor')

    def pre_lc_create_hook(self, lc_data):
        if settings.context['on_demand'] is False:
            autospotting = self.role_def().get('auto_spotting')
            if autospotting is not None:
                logging.info("Using autospotting, overrides the generic spot settings.")
            else:
                logging.info("Using regular spot, not using autospotting.")
                self.update_spot_price(lc_data)
        else:
            logging.info("--on-demand flag is set, skipping update spot price.")

    def write_deployment_summary(self, *args, **kwargs):
        from aws_deploy.tools.teamcity_api import TC
        return TC.report_status(status=True, message="Deployed release:%s/%s, ASG: %s" % (
            settings.context['bld'],settings.context.get('branch', 'no-branch'), self.asg_name_template() % settings.context))


    def enhance_parser(self, parser):
        parser.add_argument('--ami-override', help='override the ami', default=None)
        parser.add_argument('--spot-percent', help='override the percentage of the spot pricing', default=None)
        parser.add_argument('--on-demand', required=False, default=False, action='store_true',
                            help='set this flag to force on-demand instances (prevent using spots)')
        return parser

    def get_keyname(self):
        return self.key_names[self.env.lower()]

    def asg_name_template(self):
        return "%(role)s_%(env_code)s_%(bld)s_%(ts)s"
        #       majdPetclinic_staging_59_23Jun_080944
    

    def user_data(self, context):
        uesrData = []

        the_dict = {}

        the_dict['ASG_ID'] = self.asg_name_template() % settings.context

        ret_val = """#!/bin/bash
apt-get update -y
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
apt install unzip
unzip awscliv2.zip
./aws/install

apt-get install openjdk-11-jdk -y

# BLD , BRANCH , CHEF_ROLE
aws s3 cp s3://majd-petclininc-artifacts/Artifacts/^CHEF_ROLE/^BRANCH/^BLD/spring-petclinic-2.4.2.jar /home/ubuntu/petclinic.jar
aws s3 cp s3://majd-petclininc-artifacts/Artifacts/application-mysql.properties /home/ubuntu/application-mysql.properties
echo -e '\n#!/bin/bash\njava -jar -Dspring.profiles.active=mysql /home/ubuntu/petclinic.jar --spring.config.location=/home/ubuntu/application-mysql.properties' > /home/ubuntu/run-app.sh

echo -e '[Unit]\nDescription=Deployer - PetClinic
\n[Service]
User=ubuntu
ExecStart=/bin/bash /home/ubuntu/run-app.sh
SuccessExitStatus=143
TimeoutStopSec=10
Restart=on-failure
RestartSec=5

\n[Install]
WantedBy=multi-user.target
' > /etc/systemd/system/petclinic.service

chmod +x /home/ubuntu/run-app.sh
systemctl daemon-reload	
systemctl enable petclinic.service
systemctl start petclinic
systemctl status petclinic

        """ % the_dict
        print("user data script #############\n\n\n\n\n")
        print(ret_val)
        return ret_val

# def convertListToDict(lst):
#     res_dct = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}
#     return res_dct

def get_settings_lambda(*args, **kwargs):
    """
    Reference implementation Callback to get the actual configuration.
    :param args: positional params passed to the initialization
    :param kwargs: keyword params passed to the initialization
    :return: The customization object
    """
    print ("Loading the Reference settings customization: %s / %s" % (__file__, __name__))

    # if dynamic parameters are needed they can be pulled from argparse or other
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('-e', '--env', default=None, help='env')

    argc, argv = parser.parse_known_args()
    # use the params when calling the constructor

    return SampleDeploySettings(*args, **kwargs)
