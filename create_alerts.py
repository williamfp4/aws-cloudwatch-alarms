import boto3
import re

region = 'us-east-1'
account = ''
sns_name = ''
alarms = ['CPUUtilization','StatusCheck','MemoryUtilization','DiskUtilization']

cw = boto3.client('cloudwatch', region_name='us-east-1')

def get_config_info():
    customer_info = []
    instance_name = ''
    so = ''
    answer = 'n'

    while answer == 'n' or answer == '':
        customer_info.append(input("Digite o cliente: "))
        customer_info.append(input("Insira 'CONTA_AMBIENTE' (Ex: CORE_PRD): "))
        instance_name = (input("Digite o nome da instância: "))
        print(f"\nAs informações estão corretas? (y/N)\n {customer_info}\n {instance_name}")
        answer = input()
        if answer != 'y':
            customer_info.clear()

    while True:
        so_map = {'1':"linux",'2':"windows"}
        so = input("Qual é o SO da máquina? \nLinux = 1\nWindows = 2\n\n")
        if so in so_map:
            so = so_map[so]
            break
        print("Valor inválido, tente novamente...\n")

    return assign_alarm_ids(customer_info,instance_name,so)

def assign_alarm_ids(customer_info,instance_name,so):
    identifier = ''
    id_list = []
    answer = 'n'

    for metric in alarms:
        while True:
            identifier = input("Digite o ID para o alerta de ["+metric+"]: ")
            if ''.join(re.findall("MI[0-9]{9}",identifier)) != '':
                break
            print("MI inválida, tente novamente.\n")
        id_list.append(identifier)

    return info_map(id_list,customer_info,instance_name,so)

def info_map(id_list,customer_info,instance_name,so):
    global alarms
    alarms_map = {}
    defaults = [
        {
            "linux": [80,'>'],
            "windows": [80,'GreaterThanThreshold','%'],
            "namespace": "AWS/EC2"
        },
        {
            "linux": [0, '>'],
            "windows": [0, 'GreaterThanThreshold',''],
            "namespace": "AWS/EC2"
        },
        {
            "linux": [80, '>='],
            "windows": [90, 'GreaterThanOrEqualToThreshold','%'],
            "namespace": "CWAgent"
        },
        {
            "linux": [80, '<='],
            "windows": [10, 'LessThanOrEqualToThreshold','%'],
            "namespace": "CWAgent"
        }
    ]

    if so == 'windows':
        alarms.pop()
        alarms.append("Disk_free")

    for i in range(len(alarms)):
        alarms_map[alarms[i]] = defaults[i]
        alarms_map[alarms[i]].update({"id":id_list[i]})
        alarms_map[alarms[i]].update({"name":instance_name})

    return create_alarms(alarms_map,customer_info,so)

def create_alarms(alarms_map,customer_info,so):
    print("\nDeseja criar os alertas com as seguintes especificações? (y/N)")
    for metric in alarms:
        print("\nAlerta de ["+str(metric)+"]:")
        print("\t- Name: ["+str(alarms_map[metric]["id"])+"] "+str(customer_info[0])+"_"+str(customer_info[1])+"_"+str(alarms_map[metric]["name"]))
        print("\t- Operator:  ",alarms_map[metric][so][1])
        print("\t- Threshold: ",alarms_map[metric][so][0])
    answer = input()
    if answer != 'y':
        return 0
    print("Starting creation")
    for metric in alarms:
        cw.put_metric_alarm(
            AlarmName = f'[{alarms_map[metric]["mi"]}] {customer_info[0]}_{customer_info[1]}_{alarms_map[metric]["name"]}_{metric} {alarms_map[metric]["linux"][1]} {alarms_map[metric]["windows"][0]}{alarms_map[metric]["windows"][2]}',
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
    try:
        print("===== AWS CloudWatch Alarm Creator =====")
        get_config_info()
    except KeyboardInterrupt:
        print("\nShutting Down...")
