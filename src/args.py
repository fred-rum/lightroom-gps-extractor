import sys

_arg_value = {}

sys.argv.pop(0) # We don't need the executable name

if sys.argv:
    arg_list = sys.argv
else:
    arg_list = ['-lightroom', '-clusters',
                '-points', 'data/points.txt',
                '-google', 'facilities_google.kmz',
                '-avenza', '_facilities_avenza.kmz',
                '-caltopo', 'facilities_caltopo.json']

while arg_list:
    if arg_list[0] in ('-local-icons',
                       '-clusters',
                       '-lightroom'):
        _arg_value[arg_list.pop(0)] = True
    elif arg_list[0] in ('-points', '-google', '-avenza', '-caltopo'):
        _arg_value[arg_list.pop(0)] = arg_list.pop(1)
    else:
        print(f'Argument not recognized: {arg_list[0]}', file=sys.stderr)
        sys.exit(-1)

def arg(name):
    if name in _arg_value:
        return _arg_value[name]
    else:
        return None
