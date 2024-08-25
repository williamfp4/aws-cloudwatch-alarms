import boto3
import json
import re

region = 'us-east-1'
account = ''

cw = boto3.client('cloudwatch', region_name='us-east-1')

def get_config_info(config):
    alarms = config['alarms']
    customer_info = config['customer_info']
    instance_name = config['instance_name']
    so = config['so']

    while True:
        customer_info.append(input("Digite o cliente: "))
        customer_info.append(input("Insira 'CONTA_AMBIENTE' (Ex: CORE_PRD): "))
        instance_name = (input("Digite o nome da instância: "))
        print(f"\nAs informações estão corretas? (y/N)\n {customer_info}\n {instance_name}")
        answer = input()
        if answer == 'y':
            break
        customer_info.clear()

    while True:
        so_map = {'1':"linux",'2':"windows"}
        so = input("Qual é o SO da máquina? \nLinux = 1\nWindows = 2\n\n")
        if so in so_map:
            so = so_map[so]
            break
        print("Valor inválido, tente novamente...\n")

    return customer_info,instance_name,so

def assign_alarm_ids(config):
    alarms = config['alarms']
    id_list = []
    identifier = ''

    for metric in alarms:
        while True:
            identifier = input("Digite o ID para o alerta de ["+metric+"]: ")
            matches = re.fullmatch("MI[0-9]{9}",identifier)
            if matches:
                break
            print("MI inválida, tente novamente.\n")
        id_list.append(identifier)

    return id_list

def alarm_settings(config):
    modification = ''
    modified = []
    alarms = config['alarms']
    so = config['so']
    alarms_dict = {}
    defaults = {
        'linux': {
            "thresholds": [80,0,80,80],
            "operators": ["GreaterThanThreshold","GreaterThanThreshold","GreaterThanOrEqualToThreshold","GreaterThanThreshold"],
            "namespace": ["AWS/EC2","AWS/EC2","CWAgent","CWAgent"]
        },
        'windows': {
            "thresholds": [80,0,90,10],
            "operators": ["GreaterThanThreshold","GreaterThanThreshold","GreaterThanOrEqualToThreshold","LessThanOrEqualToThreshold"],
            "namespace": ["AWS/EC2","AWS/EC2","CWAgent","CWAgent"]
        }
    }

    if so == "windows":
        alarms.pop()
        alarms.append("Disk_free")

    alarms_dict.update({'alarms':alarms})
    alarms_dict.update(defaults[so])

    while True:
        print(f"\n{json.dumps(alarms_dict, indent=2)}")
        if input("\nAs configurações estão corretas? (y/N)\n").upper() == 'Y':
            break
        answer = input("\nQual atributo gostaria de modificar?\n 1 - Métricas\n 2 - Thresholds\n 3 - Operadores\n 4 - Namespace\n 5 - Nenhum\n\n")
        while True:
            if answer == '1':
                modification = "alarms"
                modified = input("\nDIGITE PALAVRA APÓS PALAVRA, SEGUIDA DE VÍRGULA (EX: CPU,THROUGHPUT,NETWORK,MEMÓRIA)\n")
            elif answer == '2':
                modification = "thresholds"
                modified = input("\nDIGITE NÚMERO APÓS NÚMERO, SEGUIDO DE VÍRGULA (EX: 75,1,90,35)\n")
            else:
                break
            if input("\nA modificação está correta? (y/N)\n"+modified+"\n").upper() == 'Y':
                alarms_dict.update({f'{modification}':modified})
                break
    config.update(alarms_dict)

    return config

def create_alarms(alarms_map,customer_info,so):
    print("\nDeseja criar os alertas com as seguintes especificações? (y/N)")
    for metric in alarms:
        print(f"\nAlerta de [{metric}]:")
        print(f"\t- Name: [{alarms_map[metric]['id']}] {customer_info[0]}_{customer_info[1]}_{alarms_map[metric]['instance']}")
        print(f"\t- Operator: {alarms_map[metric][so][1]}")
        print(f"\t- Threshold: {alarms_map[metric][so][0]}")
    answer = input()
    if answer != 'y':
        return 0
    print("Starting creation")
    for metric in alarms:
        cw.put_metric_alarm(
            AlarmName = f'[{alarms_map[metric]["id"]}] {customer_info[0]}_{customer_info[1]}_{alarms_map[metric]["instance"]}_{metric} {alarms_map[metric]["linux"][1]} {alarms_map[metric]["windows"][0]}{alarms_map[metric]["windows"][2]}',
            EvaluationPeriods = 1,
            Threshold = alarms_map[metric][so][0],
            ComparisonOperator = alarms_map[metric][so][1],
            TreatMissingData = 'missing',
            OKActions=[
                    f"arn:aws:sns:us-east-1:{account}:{sns_name}",
            ],
            AlarmActions=[
                    f"arn:aws:sns:us-east-1:{account}:{sns_name}",
            ],
            InsufficientDataActions=[
                    f"arn:aws:sns:us-east-1:{account}:{sns_name}",
            ],
            Namespace = alarms_map[metric]["namespace"],
            MetricName = metric,
            Period = 300,
            Statistic = 'Average'
        )

if __name__ == "__main__":
    config = {
        'alarms': ['CPUUtilization','StatusCheck','MemoryUtilization','DiskUtilization'],
        'customer_info': [],
        'sns_name': '',
        'instance_name': '',
        'so': '',
    }
    try:
        print("===== AWS CloudWatch Alarm Creator =====")
        config['customer_info'], config['instance_name'], config['so'] = get_config_info(config)
        config.update({'id_list':assign_alarm_ids(config)})
        config = alarm_settings(config)
        #create_alarms(config)
    except KeyboardInterrupt:
        print("\nShutting Down...")
    except Exception as e:
        print(f"\n[ERROR] {e}")
