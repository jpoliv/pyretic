#!/usr/bin/python

from time import time, sleep
from subprocess import call, check_output, Popen, PIPE, STDOUT, CalledProcessError
import sys as sys
import os as os
from optparse import OptionParser
from signal import SIGINT

from threading import Thread

class subprocess_output(Thread):
    
    def __init__(self,proc):
        self.proc = proc
        Thread.__init__(self)

    def run(self):
        while self.proc.poll() is None:
            line = self.proc.stdout.readline()
            print line,
            sleep(0.1)

def parseArgs():
    """Parse command-line args and return options object.
    returns: opts parse options dict"""

    desc = ( "The %prog utility creates Mininet network from the\n"
             "command line. It can create parametrized topologies,\n"
             "invoke the Mininet CLI, and run tests." )

    usage = ( '%prog [options]\n'
              '(type %prog -h for details)' )
    
    opts = OptionParser( description=desc, usage=usage )
    opts.add_option( '--verbose', '-v', action="store_true", dest="verbose")
    opts.add_option( '--quiet', '-q', action="store_true", dest="quiet")
    opts.add_option( '--clients', '-c', action="store", type="string", 
                     dest="clients", default='2', help = 'number of clients'  )
    opts.add_option( '--servers', '-s', action="store", type="string", 
                     dest="servers", default='2', help = 'number of servers'  )

    options, args = opts.parse_args()
    if options.quiet and options.verbose:
        opts.error("options -q and -v are mutually exclusive")
    return (options, args)

def main():
    
    (options, args) = parseArgs()
    if options.verbose:
        flags = ['-v']
    else:
        flags = ['-q']

    # GET PATHS
    controller_src_path = os.path.expanduser('~/pyretic/examples/static_load_balancer.py')
    unit_test_path = os.path.expanduser('~/pyretic/tests/load_balancer_unit_test.py')
    pox_path = os.path.expanduser('~/pox/pox.py')

    # MAKE SURE WE CAN SEE ALL OUTPUT IF VERBOSE
    env = os.environ.copy()
    if options.verbose:
        env['PYTHONUNBUFFERED'] = 'True'

    # STARTUP CONTROLLER
    controller = Popen([sys.executable, pox_path,'--no-cli', controller_src_path, 
                        '--clients='+options.clients, '--servers='+options.servers], 
                       env=env,
                       stdout=PIPE, 
                       stderr=STDOUT)
    if options.verbose:
        controller_out = subprocess_output(controller)
        controller_out.start()
    sleep(1)

    # TEST EACH TOPO
    topos = ['bump_clique,1,'+options.clients+','+options.servers, 'bump_clique,2,'+options.clients+','+options.servers]

    for topo in topos:
        test = ['sudo', unit_test_path, '--topo', topo] + flags
        testproc = call(test)
        if testproc == 0:
            print "%s\tCONNECTIVITY PASSED" % topo
        else:
            print "%s\tCONNECTIVITY FAILED" % topo
        
    # KILL CONTROLLER
    controller.send_signal( SIGINT )

if __name__ == '__main__':
    main()