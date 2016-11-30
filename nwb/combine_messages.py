import re
import pprint
pp = pprint.PrettyPrinter(indent=4)
    
    
def combine_messages(messages):
    """ Combines messages that have one or more integers in them, such as
    "trial001" "trial002", into a single message like "trial# (#=1-2)".
    This is to reduce the number of messages required to be displayed.
    Operates by creating the following structure, named "ti" for "template info":
    { 
      't2tn': {}  - maps each template (containing "#") to a template number (tn)
      'tn2t': [] - list of templates, indexed by the template number
      'm2tns': {} - maps each message number (index in messages) to 
          array of template numbers (tns)
      'tn2dm': {} - maps each template number to a dictionary that has as keys the digits
          used to make the template, and with value the message number used to make the template
          with those digits. i.e.:
          { tn1: {d1: m1, d2: m2}, tn2: {d3: m3, d4: m4}, tn2: { ...}}
          where:
             tn - template number
             d: m  - digits used to make template from message number m
      'mout': [] - messages to display (output), formed by combining messages
      'mfin': [] - set of message numbers "finished" (already included in mout).
    }
    This function works by first creating everything except mout and mfin, then
    going through each message, finding the template numbers that have the most
    digits, and using those to make the combined message.
    """
    ti = {}
    ti['t2tn'] = {}
    ti['tn2t'] = []
    ti['m2tns'] = {}
    ti['tn2dm'] = {}
    for mn in range(len(messages)):
        msg = messages[mn]
        found_nums = re.findall("\d+", msg)
        if not found_nums:
            # no numbers found, don't process
            continue
        # remove any duplicates
        found_nums = list(set(found_nums))
        for digits in found_nums:
            pattern = "(?<!\d)%s(?!\d)" % digits  # substitute only if digits not surrounded by other digits
            template = re.sub(pattern, "#", msg)    # make template for this message and digits
            if template not in ti['t2tn']:
                tn = len(ti['tn2t'])    # template number
                ti['tn2t'].append(template)  # add template to list of templates
                ti['t2tn'][template] = tn    # add entry to map of template to template number
            else:
                tn = ti['t2tn'][template]
            # save template number (tn) in 'm2tns'
            if mn not in ti['m2tns']:
                ti['m2tns'][mn] = [tn,]
            else:
                ti['m2tns'][mn].append(tn)
            # save template number, digits and message number in 'tn2dm'
            if tn not in ti['tn2dm']:
                ti['tn2dm'][tn] = {digits: mn}
            else:
                if digits in ti['tn2dm'][tn]:
                    print ("duplicate message found: %s" % msg)
                    break
                ti['tn2dm'][tn][digits] = mn
    # done building needed structures.  Now generate 'output' (i.e. ti['mfin'] and ti['mout']
    ti['mout'] = []
    ti['mfin'] = set([])
    for mn in range(len(messages)):
        if mn in ti['mfin']:
            # message has already been displayed (using a template)
            continue
        if mn not in ti['m2tns']:
            # no digits found in this message, just display as is
            ti['mout'].append(messages[mn])
            ti['mfin'].add(mn)
            continue
        # this message has at least one pattern.  Find template with largest number of other messages
        nmax = 0
        for tn in ti['m2tns'][mn]:
            if len(ti['tn2dm'][tn]) > nmax:
                max_tn = tn
                nmax = len(ti['tn2dm'][tn])
        # if no other messages use pattern, just display as is
        if nmax == 1:
            ti['mout'].append(messages[mn])
            ti['mfin'].add(mn)
            continue
        # other messages use this template.  Get list message numbers and digits that share this template
        s_digits = ti['tn2dm'][max_tn].keys()  # shared digits
        s_mns = ti['tn2dm'][max_tn].values()   # shared message numbers
        # make new message by combining shared digits with template
        template = ti['tn2t'][max_tn]
        # convert digits from string to int
        i_digits = sorted([int(i) for i in s_digits])
#         if len(i_digits) == 4:
#             import pdb; pdb.set_trace()
        # make string representing ranges of digits
        prevn = i_digits[0]  # initialize previous number to first
        sr = str(prevn)      # string of ranges being generated
        in_range = False
        for i in range(1, len(i_digits)):
            newn = i_digits[i]
            if newn == prevn + 1:
                # in a range
                in_range = True
            else:
                # not in a range.  But if was previously save end of previous range
                if in_range:
                    sr = "%s-%i" % (sr, prevn)
                    in_range = False
                # save new number
                sr = "%s,%i" % (sr, newn)
            prevn = newn
        # append final number if in range
        if in_range:
             sr = "%s-%i" % (sr, newn)
        new_message = template + " (#=%s)" % sr
        ti['mout'].append(new_message)
        # add all messages that share this template to ti['mfin'] so they are not displayed again
        ti['mfin'].update(s_mns)
    # return list of combined messages
    return ti['mout']
    
    
    
def test_combine_messages():
    """ tests combine_messages function"""
    messages = [
    "some prefix trial-none",
    "some prefix trial23",
    "some prefix trial23/timestamps",
    "some prefix trial23 timestamps",
    "some prefix trial23\ntimestamps",
    "some prefix 32-bits, trial32",
    "some prefix 32-bits, trial33",
    "some prefix 32-bits, trial34",
    "some prefix 32-bits, trial35",
    "some prefix trial-11",
    "some prefix trial23 and trial23 again",
    "some prefix trial27",
    "some prefix trial27/timestamps",
    "some prefix trial27 timestamps",
    "some prefix trial27\ntimestamps",
    "some prefix 32-bits, trial27",
    "some prefix trial27 and trial27 again"]
    cm = combine_messages(messages)
    pp.pprint(cm)
    
if __name__ == '__main__':
    test_combine_messages()
    
