This is an Updated Version of the original "Nimble Storage Hardware Health API Check Script" from geekmungus.
We use it mainly to monitor physical Nimble disks which is not possible with the current snmp check.
Its Python 3 compatible and works with check mk 2.4.0px


Example usage in Check MK:

Upload the script to ~/local/lib/nagios/plugins/ and make it executebale: "chmod +x..."
Create new "Integrate Nagios plug-ins" rule in Check MK
In command line specify: ~/local/lib/nagios/plugins/check_nimble_health_api.py -e https://xxxx:5392 -u user -p password


