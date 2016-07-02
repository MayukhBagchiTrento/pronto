import json
import functools

from pronto import utils
from pronto.relationship import RSHIPS


class Term(object):
    """ An ontology term.
    """

    def __init__(self, cid, name, desc, relations = {} , other={}):
        self.id = cid
        self.name = name
        self.desc = desc
        self.relations = relations
        self.other = other

    def __repr__(self):
        return "<{}: {}>".format(self.id, self.name)

    @property
    @functools.lru_cache(None)
    def parents(self):
        parents = TermList()
        for parental_rship in ('is_a', 'is_part', 'part_of'):
            if parental_rship in self.relations.keys():
                parents.extend(self.relations[parental_rship])
        return parents

    @property
    #@utils.memoize
    def children(self):
        children = TermList()
        for children_rship in ('has_part', 'can_be'):
            if children_rship in self.relations.keys():
                children.extend(self.relations[children_rship])
        return children

    @property
    def obo(self):

        obo =  '[Term]' + '\n'
        obo += 'id: {}'.format(self.id) + '\n'
        obo += 'name: {}'.format(self.name) + '\n'
        
        if self.desc: 
            obo += 'def: {}'.format(self.desc) + '\n'
        
        # add more bits of information
        for k,v in self.other.items():
            if isinstance(v, list):
                for x in v:
                    obo += '{}: {}'.format(k,x) + '\n'        
            else:
                obo += '{}: {}'.format(k,v) + '\n'

        # add relationships (only bottom up ones)
        for relation,companions in self.relations.items():
            if relation in RSHIPS:

                for companion in companions:

                    if relation != 'is_a':
                        obo += 'relationship: '
                    obo += '{}: '.format(relation)
                    
                    if isinstance(companion, Term):
                        obo += '{} ! {}'.format(companion.id, companion.name) + '\n'
                    else:
                        obo += '{}'.format(companion)
                        obo += '\n'

        return obo

    def rchildren(self, level=-1, intermediate=True):
        """Create a recursive list of children.

        Note that the :param:`intermediate` can be used to include every 
        child to the returned list, not only the most nested ones.
        
        """
        rchildren = []

        if level==0:
            return []

        if self.children:
            
            if intermediate or level==1:
                rchildren.extend(self.children)

            for child in self.children:
                rchildren.extend(child.rchildren(level=level-1, 
                                                 intermediate=intermediate))

        return TermList(set(rchildren))

    @property    
    def __deref__(self):
        """A dereferenced 

        Relations dictionary only contains other Terms id to avoid 
        circular references when 
        """
        jsondict = {
            'id':        self.id , 
            'name':      self.name,
            'other':     self.other,
            'desc':      self.desc,
            'relations': {k:v.id for k,v in self.relations.items()}
         }

        return jsondict


class TermList(object):
    """A list of Terms.

    TermList behaves exactly like a list, except it contains shortcuts to 
    generate lists of terms' attributes.

    :Example:

    >>> from pronto import OwlXML
    >>> nmr = OwlXML('http://nmrml.org/cv/v1.0.rc1/nmrCV.owl')
    >>> type(nmr['NMR:1000031'].children)
    <class 'pronto.term.TermList'>

    Use a shortcut:
    >>> nmr['NMR:1000031'].children.id
    ['NMR:1000122', 'NMR:1000156', 'NMR:1000157', 'NMR:1000489']
    >>> nmr['NMR:1400014'].relations['is_a']
    [<NMR:1400011: cardinal part of NMR instrument>]

    """

    def __init__(self, *elements):
        if not elements:
            self.terms = []
        elif len(elements)==1:
            if isinstance(elements[0], list):
                self.terms = elements[0].copy()
            elif isinstance(elements[0], set):
                self.terms = list(elements[0])
        else:
            self.terms = [term for term in elements]
        self._check_content()

    def _check_content(self):
        for term in self.terms:
            if not isinstance(term, Term):
                raise TypeError('TermList can only contain Terms.')

    def __repr__(self):
        return self.terms.__repr__()

    def __iter__(self):
        return self.terms.__iter__()

    def __getattr__(self, attr):
        if attr in ['children', 'parents']:
            return TermList( [ y for x in self.terms for y in getattr(x, attr)] )
        elif attr in ['id', 'name', 'desc', 'other']:
            return [getattr(x, attr) for x in self.terms]
        else:
            return getattr(self.terms, attr)

    def __getitem__(self, item):
        return self.terms[item]


