from numpy import float64
from brian2.codegen.specifiers import (Function, Value, ArrayVariable,
                                       Subexpression, Index)
from brian2.codegen.translation import translate, make_statements
from brian2.codegen.languages import CLanguage, PythonLanguage, CUDALanguage
from brian2.codegen.templating import apply_code_template
from brian2.utils.stringtools import deindent

# TODO: bug in CLanguage (V = Vr has no dtype)

# we don't actually use these, but this is what we would start from
reset = '''
V = Vr
'''

abstract = '''
V = Vr
'''

specifiers = {
    'V':ArrayVariable('_array_V', float64),
    'Vr':ArrayVariable('_array_Vr', float64),
    '_neuron_idx':Index(all=False),
    }

def template(lang):
    if isinstance(lang, CUDALanguage):
        return deindent('''
        __global__ reset(int _num_spikes)
        {
            const int _spike_idx = threadIdx.x+blockIdx.x*blockDim.x;
            if(_spike_idx>=_num_spikes) return;
            const int _neuron_idx = _spikes[_spike_idx];
            %CODE%
        }
        ''')
    elif isinstance(lang, CLanguage):
        return deindent('''
        for(int _spike_idx=0; _spike_idx<_num_spikes; _spike_idx++)
        {
            const int _neuron_idx = _spikes[_spike_idx];
            %CODE%
        }
        ''')
    elif isinstance(lang, PythonLanguage):
        return deindent('''
        _neuron_idx = _spikes
        %CODE%
        ''')

intermediate = make_statements(abstract, specifiers, float64)

print 'RESET:'
print reset
print 'ABSTRACT CODE:'
print abstract
print 'INTERMEDIATE STATEMENTS:'
print
for stmt in intermediate:
    print stmt
print

for lang in [
        PythonLanguage(),
        CLanguage(),
        CUDALanguage(),
        ]:
    innercode = translate(abstract, specifiers, float64, lang)
    code = apply_code_template(innercode, template(lang))
    print lang.__class__.__name__
    print '='*len(lang.__class__.__name__)
    print code