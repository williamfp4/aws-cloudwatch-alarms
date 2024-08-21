import boto3
import re

cw = boto3.client('cloudwatch',region_name='us-east-1')

cliente = []
account = "848767713384"
so = ''
instance_name = ''
sns_name = ''
mi_list = []
alarms = ["CPUUtilization","StatusCheck","MemoryUtilization","Disk_free"]
alarms_map = {}

def select_mis():
    mi = ''
    answer = 'n'
    validation = False
    global mi_list, so, cliente, instance_name

    print("===== Bem Vindo =====")
    while answer == 'n' or answer == '':
        cliente.append(input("Digite o cliente: "))
        cliente.append(input("Informe o ambiente/conta da instância (Ex: CORP_PRD): "))
        instance_name = (input("Digite o nome da instância: "))
        print("\nAs informações estão corretas? (y/N)\n",cliente,instance_name)
        answer = input()
        if answer != 'y':
            cliente.clear()
    while validation == False:
        so = input("Qual é o SO da máquina? \nLinux = 1\nWindows = 2\n\n")
        if so == '1':
            so = "linux"
            validation = True
        elif so == '2':
            so = "windows"
            validation = True
        else:
            print("Valor inválido, tente novamente...")
    validation = False
    for metric in alarms:
        while validation == False:
            mi = input("Digite a MI de ["+metric+"]: ")
            if ''.join(re.findall("MI[0-9]{9}",mi)) == '':
                validation = False
                print("MI inválida, tente novamente.\n")
            else:
                validation = True
        validation = False
        mi_list.append(mi)
    return info_map()

def info_map():
    global mi_list,alarms,alarms_map,instance_name
    defaults = [{
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
    }]
    for i in range(len(alarms)):
        alarms_map[alarms[i]] = defaults[i]
        alarms_map[alarms[i]].update({"mi":mi_list[i]})
        alarms_map[alarms[i]].update({"name":instance_name})
    create_alarms()

def create_alarms():
    global cliente,so,alarms_map,account,alarms
    print("\nDeseja criar os alertas com as seguintes especificações? (y/N)")
    for metric in alarms:
        print("\nAlerta de ["+str(metric)+"]:")
        print("\t- Name: ["+str(alarms_map[metric]["mi"])+"] "+str(cliente[0])+"_"+str(cliente[1])+"_"+str(alarms_map[metric]["name"]))
        print("\t- Operator:  ",alarms_map[metric][so][1])
        print("\t- Threshold: ",alarms_map[metric][so][0])
    answer = input()
    if answer != 'y':
        return 0
    print("Starting creation")
    for metric in alarms:
        cw.put_metric_alarm(
            AlarmName = f'[{alarms_map[metric]["mi"]}] {cliente[0]}_{cliente[1]}_{alarms_map[metric]["name"]}_{metric} {alarms_map[metric]["linux"][1]} {alarms_map[metric]["windows"][0]}{alarms_map[metric]["windows"][2]}',
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
	select_mis()
