import functions

if __name__ == "__main__":
    # initialize ec2 client and config
    client=functions.ec2_client()
    config=functions.read_config()
    
    # deploy infrastructure defined in config
    functions.create_vpc(client, config)
    functions.create_attach_igw(client, config)
    functions.create_subnet(client, config)
    functions.create_rtbl(client, config)
    functions.create_route(client, config)
    functions.create_sg(client, config)
    functions.create_key(client, config)
    functions.create_ec2(client, config)
    
    # output updated config file
    functions.output_file(config)