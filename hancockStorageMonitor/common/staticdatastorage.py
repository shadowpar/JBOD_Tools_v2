from pathlib import Path
from collections import OrderedDict

BASEPATH = Path(__file__).parent.absolute().parent.absolute().parent.absolute().joinpath('flatdata')

EXPERIMENTS = ['star', 'phenix', 'atlas', 'sphenix', 'belle2', 'dune']
experimentHostListsEXPERIMENTHOSTLISTS = {experiment:BASEPATH.joinpath(Path(experiment + 'hosts.lst')) for experiment in EXPERIMENTS}
allhosts = {experiment:experimentHostListsEXPERIMENTHOSTLISTS[experiment].read_text().splitlines(keepends=False) for experiment in experimentHostListsEXPERIMENTHOSTLISTS}
SEVERITYLEVELS = ['low', 'medium', 'high']
ERRORTYPES2SEVERITY = OrderedDict({'olddata':SEVERITYLEVELS[2], 'smartstatus':SEVERITYLEVELS[1], 'sasdisknoarray':SEVERITYLEVELS[0], 'uncorrectederrors':SEVERITYLEVELS[1], 'growndefects':SEVERITYLEVELS[1],
                        'missingrecords':SEVERITYLEVELS[2], 'raidarraystate':SEVERITYLEVELS[2], 'failedpaths':SEVERITYLEVELS[1], 'failedcables':SEVERITYLEVELS[2]})
CABLESPERJBOD = 2 #The normal number of SAS cables per JBOD
NEWJBODMODELS = ['scaleapex 4u102', 'h4102-j']#,'h4060-j']
VALIDDISKCOUNTS = [60,84,102]