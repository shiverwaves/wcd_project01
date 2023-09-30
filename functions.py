import boto3
import json
import time
import pprint

def ec2_client():
    return boto3.client('ec2', region_name='us-east-1')


def read_config():
    with open('config.json', 'r') as openfile:
        config=json.load(openfile)
    return config


def create_vpc(ec2, config):
    vpc_name=config["vpc_name"]
    vpc_cidr=config["vpc_cidr"]
    tag_specs=[
        {"ResourceType": "vpc",
            "Tags": [
                {"Key": "Name", "Value": vpc_name},
                {"Key": "project", "Value": "wecloud"}
            ] 
        }
    ]
    vpc=ec2.create_vpc(
        CidrBlock=vpc_cidr,
        TagSpecifications=tag_specs)
    time.sleep(1)
    config.update({"vpc_id" : vpc['Vpc']['VpcId']})
    pprint.pprint(vpc)


def create_attach_igw(client, config):
    vpc_id=config["vpc_id"]
    igw_name=config["igw_name"]
    tag_specs=[
        {"ResourceType": "internet-gateway",
            "Tags": [
                {"Key": "Name", "Value": igw_name},
                {"Key": "project", "Value": "wecloud" }
            ] 
        }
    ]
    igw=client.create_internet_gateway(
        TagSpecifications=tag_specs)
    time.sleep(1)
    client.attach_internet_gateway(
        VpcId=vpc_id,
        InternetGatewayId=igw['InternetGateway']['InternetGatewayId'])
    time.sleep(1)
    config.update({ "igw_id" : igw['InternetGateway']['InternetGatewayId']})
    pprint.pprint(igw)


def create_subnet(client, config):
    vpc_id=config["vpc_id"]
    subnet_name=config["subnet_name"]
    subnet_cidr=config["subnet_cidr"]
    tag_specs=[
        {"ResourceType": "subnet",
            "Tags": [
                {"Key": "Name", "Value": subnet_name},
                {"Key": "project", "Value": "wecloud" }
            ] 
        }
    ]
    subnet=client.create_subnet(
        VpcId=vpc_id,
        CidrBlock=subnet_cidr,
        TagSpecifications=tag_specs)
    time.sleep(1)
    config.update({"subnet_id" : subnet['Subnet']['SubnetId']})
    
    client.modify_subnet_attribute(
        SubnetId=subnet['Subnet']['SubnetId'],
        MapPublicIpOnLaunch={"Value" : True})
    time.sleep(1)
    
    pprint.pprint(subnet)
    

def create_rtbl(client, config):
    vpc_id=config["vpc_id"]
    subnet_id=config["subnet_id"]
    rtbl_name=config["rtbl_name"]
    tag_specs=[
        {"ResourceType": "route-table",
            "Tags": [
                {"Key": "Name", "Value": rtbl_name},
                {"Key": "project", "Value": "wecloud"}
            ] 
        }
    ]
    rtbl=client.create_route_table(
        VpcId=vpc_id,
        TagSpecifications=tag_specs)
    time.sleep(1)
    client.associate_route_table(
        RouteTableId=rtbl['RouteTable']['RouteTableId'],
        SubnetId=config["subnet_id"])
    time.sleep(1)
    config.update({"rtbl_id" : rtbl['RouteTable']['RouteTableId']})
    pprint.pprint(rtbl)
    
    
def create_route(client, config):
    rtbl_id=config["rtbl_id"]
    igw_id=config["igw_id"]
    rt_dest=config["rt_dest"]
    rt=client.create_route(
        RouteTableId=rtbl_id,
        DestinationCidrBlock=rt_dest,
        GatewayId=igw_id)
    time.sleep(1)
    pprint.pprint(rt)


def create_sg(client, config):
    vpc_id=config['vpc_id']
    sg_name=config['sg_name']
    sg_descr=config['sg_descr']
    tag_specs=[
        {"ResourceType": "security-group",
            "Tags": [
                {"Key": "Name", "Value": sg_name},
                {"Key": "project", "Value": "wecloud"}
            ] 
        }
    ]
    sg=client.create_security_group(
        GroupName=sg_name,
        VpcId=vpc_id,
        Description=sg_descr,
        TagSpecifications=tag_specs)
    time.sleep(1)
    sg_rule=client.authorize_security_group_ingress(
        GroupId=sg['GroupId'],
        IpPermissions=config['sg_rules']
    )
    time.sleep(1)
    config.update({"sg_id" : sg['GroupId']})
    pprint.pprint(sg)
    pprint.pprint(sg_rule)


def create_key(client, config):
    tag_specs=[
        {"ResourceType": "key-pair",
            "Tags": [
                {"Key": "Name", "Value": config['key_name']},
                {"Key": "project", "Value": "wecloud"}
            ] 
        }
    ]
    key=client.create_key_pair(
        KeyName=config['key_name'],
        KeyType='rsa',
        KeyFormat='pem',
        TagSpecifications=tag_specs
        
    )
    time.sleep(1)
    
    key_file=open(config["key_name"],"w")
    key_file.write(key['KeyMaterial'])
    key_file.close
    pprint.pprint(key)
    config.update({"key" : key['KeyMaterial']})
    
    
def create_ec2(client, config):
    for instance in config['instances']:
        tag_specs=[
            {"ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": instance['ins_name']},
                    {"Key": "project", "Value": "wecloud"}
                ] 
            }
        ]
        ins=client.run_instances(
            ImageId=instance['ami_id'],
            InstanceType=instance['ins_type'],
            KeyName=config['key_name'],
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[config['sg_id']],
            SubnetId=config['subnet_id'],
            TagSpecifications=tag_specs
        )
        time.sleep(1)
        pprint.pprint(ins)
        instance.update({"ins_id": ins['Instances'][0]['InstanceId']})
        server=client.describe_instances(InstanceIds=[instance['ins_id']])
        instance.update({"ins_pub-ip": server['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']})
        instance.update({"ins_priv-ip":server['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['PrivateIpAddress']})
    
      
def output_file(config):
    config_file=open("wcd_project01.json", "w")
    config_file.write(json.dumps(config, sort_keys=True, indent=2))
    config_file.close
