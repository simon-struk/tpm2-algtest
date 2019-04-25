import os
import subprocess
import zipfile
import argparse
import sys
import glob
import csv

device = '/dev/tpm0'
image_tag = 'v0.5'

def zip():
    zipf = zipfile.ZipFile('out.zip', 'w', zipfile.ZIP_DEFLATED)
    for file in os.listdir('out'):
        zipf.write('out/' + file)

def quicktest():
    run_command = ['docker', 'run', '-it', '--init', '--device=' + device,
            '--entrypoint=tpm2_getcap', 'simonstruk/tpm2-algtest:' + image_tag]
    print('Running quicktest...')
    with open('out/Quicktest_algorithms.txt', 'w') as outfile:
        subprocess.run(run_command + ['-c', 'algorithms'], stdout=outfile).check_returncode()
    with open('out/Quicktest_commands.txt', 'w') as outfile:
        subprocess.run(run_command + ['-c', 'commands'], stdout=outfile).check_returncode()
    with open('out/Quicktest_properties-fixed.txt', 'w') as outfile:
        subprocess.run(run_command + ['-c', 'properties-fixed'], stdout=outfile).check_returncode()
    with open('out/Quicktest_properties-variable.txt', 'w') as outfile:
        subprocess.run(run_command + ['-c', 'properties-variable'], stdout=outfile).check_returncode()
    with open('out/Quicktest_ecc-curves.txt', 'w') as outfile:
        subprocess.run(run_command + ['-c', 'ecc-curves'], stdout=outfile).check_returncode()
    with open('out/Quicktest_handles-persistent.txt', 'w') as outfile:
        subprocess.run(run_command + ['-c', 'handles-persistent'], stdout=outfile).check_returncode()

def add_args(run_command, args):
    if args.num:
        run_command += [ '-n', str(args.num) ]
    if args.duration:
        run_command += [ '-d', str(args.duration) ]
    if args.keytype:
        run_command += [ '-t', args.keytype ]
    if args.keylen:
        run_command += [ '-l', str(args.keylen) ]
    if args.curveid:
        run_command += [ '-C', str(args.curveid) ]
    if args.command:
        run_command += [ '-c', args.command ]

def run_image(run_command, logfile):
    proc = subprocess.Popen(run_command, stdout=subprocess.PIPE, universal_newlines=True)
    for line in proc.stdout:
        sys.stdout.write(line + '\r')
        logfile.write(line)
    proc.wait()

def compute_rsa_privates(filename):
    def extended_euclidean(a, b):
        x0, x1, y0, y1 = 0, 1, 1, 0
        while a != 0:
            q, b, a = b // a, a, b % a
            y0, y1 = y1, y0 - q * y1
            x0, x1 = x1, x0 - q * x1
        return b, x0, y0

    def mod_exp(base, exp, n):
        res = 1
        base %= n
        while exp > 0:
            if exp % 2 == 1:
                res *= base
                res %= n
            exp //= 2
            base *= base
            base %= n
        return res

    def compute_row(row):
        try:
            n = int(row['n'], 16)
            e = int(row['e'], 16)
            p = int(row['p'], 16)
        except Exception:
            print(f"Cannot compute row {row['id']}")
            return
        q = n // p
        totient = (p - 1) * (q - 1)
        _, d, _ = extended_euclidean(e, totient)
        d %= totient

        message = 12345678901234567890
        assert mod_exp(mod_exp(message, e, n), d, n) == message, \
            f"something went wrong (row {row['id']})"

        row['q'] = '%X' % q
        row['d'] = '%X' % d

    rows = []
    with open(filename) as infile:
        reader = csv.DictReader(infile, delimiter=';')
        for row in reader:
            rows.append(row)

    for row in rows:
        compute_row(row)

    with open(filename, 'w') as outfile:
        writer = csv.DictWriter(
                outfile, delimiter=';', fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def keygen(args):
    run_command = [ 'docker', 'run', '-it', '--init', '--device=' + device,
            '--volume=' + os.getcwd() + '/out:/tpm2-algtest/build/out:z',
            'simonstruk/tpm2-algtest:' + image_tag, '-T', 'device', '-s', 'keygen' ]
    add_args(run_command, args)

    print('Running keygen test...')
    with open('out/keygen_log.txt', 'w') as logfile:
        run_image(run_command, logfile)

    print('Computing RSA private keys...')
    for filename in glob.glob("out/Keygen_RSA_*_keys.csv"):
        print(filename)
        compute_rsa_privates(filename)

def perf(args):
    run_command = [ 'docker', 'run', '-it', '--init', '--device=' + device,
            '--volume=' + os.getcwd() + '/out:/tpm2-algtest/build/out:z',
            'simonstruk/tpm2-algtest:' + image_tag, '-T', 'device', '-s', 'perf' ]
    add_args(run_command, args)

    print('Running perf test...')
    with open('out/perf_log.txt', 'w') as logfile:
        run_image(run_command, logfile)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('test', metavar='test', type=str)
    parser.add_argument('-n', '--num', type=int, required=False)
    parser.add_argument('-d', '--duration', type=int, required=False)
    parser.add_argument('-t', '--keytype', type=str, required=False)
    parser.add_argument('-l', '--keylen', type=int, required=False)
    parser.add_argument('-C', '--curveid', type=int, required=False)
    parser.add_argument('-c', '--command', type=str, required=False)
    args = parser.parse_args()

    if not os.path.exists(device):
        print(f'Device {device} not found')
        return

    print('IMPORTANT: Please do not suspend or hibernate the computer while testing the TPM!')

    if args.test == 'quicktest':
        os.makedirs('out', exist_ok=True)
        quicktest()
        zip()
    elif args.test == 'keygen':
        os.makedirs('out', exist_ok=True)
        keygen(args)
        zip()
    elif args.test == 'perf':
        os.makedirs('out', exist_ok=True)
        perf(args)
        zip()
    elif args.test == 'fulltest':
        os.makedirs('out', exist_ok=True)
        with open('out/docker_info.txt', 'w') as f:
            f.write('image ' + image_tag)
        quicktest()
        keygen(args)
        perf(args)
        zip()
        print('The tests are finished. Thank you! Please send the generated file (out.zip) to xstruk@fi.muni.cz')
    else:
        print('invalid test type, needs to be one of: fulltest, quicktest, keygen, perf')

if __name__ == '__main__':
    main()
