from anki.sched import Scheduler
from aqt.deckbrowser import DeckBrowser
from operator import itemgetter
from aqt.qt import *
from aqt.utils import askUser, getOnlyText, openLink, showWarning, shortcut, \
    openHelp, downArrow
import math
import aqt
import itertools
def deckDueList(self):
    "Returns [deckname, did, rev, lrn, new, new_unlim]"
    self._checkDay()
    self.col.decks.recoverOrphans()
    decks = self.col.decks.all()
    decks.sort(key=itemgetter('name'))
    lims = {}
    data = []
    def parent(name):
        parts = name.split("::")
        if len(parts) < 2:
            return None
        parts = parts[:-1]
        return "::".join(parts)
    for deck in decks:
        # if we've already seen the exact same deck name, remove the
        # invalid duplicate and reload
        if deck['name'] in lims:
            self.col.decks.rem(deck['id'], cardsToo=False, childrenToo=True)
            return self.deckDueList()
        p = parent(deck['name'])
        # new
        nlim = self._deckNewLimitSingle(deck)
        if p:
            if p not in lims:
                # if parent was missing, this deck is invalid, and we
                # need to reload the deck list
                self.col.decks.rem(deck['id'], cardsToo=False, childrenToo=True)
                return self.deckDueList()
            nlim = min(nlim, lims[p][0])
        new = self._newForDeck(deck['id'], nlim)
        new_unlim = self._newForDeck(deck['id'], 1000000000)
        # learning
        lrn = self._lrnForDeck(deck['id'])
        # reviews
        rlim = self._deckRevLimitSingle(deck)
        if p:
            rlim = min(rlim, lims[p][1])
        rev = self._revForDeck(deck['id'], rlim)
        # save to list
        data.append([deck['name'], deck['id'], rev, lrn, new, 0, new_unlim])
        # add deck as a parent
        lims[deck['name']] = [nlim, rlim]
    return data
def _groupChildrenMain(self, grps):
    tree = []
    # group and recurse
    def key(grp):
        return grp[0][0]
    for (head, tail) in itertools.groupby(grps, key=key):
        tail = list(tail)
        did = None
        rev = 0
        new = 0
        new_unlim = 0
        lrn = 0
        children = []
        for c in tail:
            if len(c[0]) == 1:
                # current node
                did = c[1]
                rev += c[2]
                lrn += c[3]
                new += c[4]
                new_unlim += c[6]
            else:
                # set new string to tail
                c[0] = c[0][1:]
                children.append(c)
        children = self._groupChildrenMain(children)
        # tally up children counts
        for ch in children:
            rev += ch[2]
            lrn += ch[3]
            new += ch[4]
            new_unlim += ch[6]
        # limit the counts to the deck's limits
        conf = self.col.decks.confForDid(did)
        deck = self.col.decks.get(did)
        burn = 0.0
        npd = 0
        if not conf['dyn']:
            rev = max(0, min(rev, conf['rev']['perDay']-deck['revToday'][1]))
            new = max(0, min(new, conf['new']['perDay']-deck['newToday'][1]))
            npd = conf['new']['perDay']
        new_today = new_unlim - new
        if new > 0:
            burn += 1.0
        if npd > 0:
            burn += float(new_today) / float(npd)

        tree.append((head, did, rev, lrn, new, children, burn))
    return tuple(tree)

def _renderDeckTree(self, nodes, depth=0):
    if not nodes:
        return ""
    if depth == 0:
        buf = """
<tr><th colspan=5 align=left>%s</th><th class=count>%s</th>
<th class=count>%s</th><th class=count>%s</th><th class=count></th></tr>""" % (
        _("Deck"), _("Due"), _("New"), "Days")
        buf += self._topLevelDragRow()
    else:
        buf = ""
    for node in nodes:
        buf += self._deckRow(node, depth, len(nodes))
    if depth == 0:
        buf += self._topLevelDragRow()
    return buf
def _deckRow(self, node, depth, cnt):
    name, did, due, lrn, new, children, burn = node
    deck = self.mw.col.decks.get(did)
    if did == 1 and cnt > 1 and not children:
        # if the default deck is empty, hide it
        if not self.mw.col.db.scalar("select 1 from cards where did = 1"):
            return ""
    # parent toggled for collapsing
    for parent in self.mw.col.decks.parents(did):
        if parent['collapsed']:
            buff = ""
            return buff
    prefix = "-"
    if self.mw.col.decks.get(did)['collapsed']:
        prefix = "+"
    due += lrn
    def indent():
        return "&nbsp;"*6*depth
    if did == self.mw.col.conf['curDeck']:
        klass = 'deck current'
    else:
        klass = 'deck'
    buf = "<tr class='%s' id='%d'>" % (klass, did)
    # deck link
    if children:
        collapse = "<a class=collapse href='collapse:%d'>%s</a>" % (did, prefix)
    else:
        collapse = "<span class=collapse></span>"
    if deck['dyn']:
        extraclass = "filtered"
    else:
        extraclass = ""
    buf += """

    <td class=decktd colspan=5>%s%s<a class="deck %s" href='open:%d'>%s</a></td>"""% (
        indent(), collapse, extraclass, did, name)
    def nonzeroColour(cnt, colour, extra=""):
        if not cnt:
            colour = "#e0e0e0"
        if cnt >= 1000:
            cnt = "1000+"
        return "<font color='%s'>%s%s</font>" % (colour, extra, cnt)
    burnfrac, burnint = math.modf(burn)
    burndisp = ""
    burndisp2 = ""
    if burnfrac > 0.0:
        burndisp = "*"
    buf += "<td align=right>%s</td><td align=right>%s</td><td align=right>%s</td>" % (
            nonzeroColour(due, "#007700"),
            nonzeroColour(new, "#000099", ""),
            nonzeroColour(int(burnint), "#990000", burndisp))
    # options
    buf += "<td align=right class=opts>%s</td></tr>" % self.mw.button(
        link="opts:%d"%did, name="<img valign=bottom src='qrc:/icons/gears.png'>"+downArrow())
    # children
    buf += self._renderDeckTree(children, depth+1)
    return buf

Scheduler.deckDueList = deckDueList
Scheduler._groupChildrenMain = _groupChildrenMain
DeckBrowser._renderDeckTree = _renderDeckTree
DeckBrowser._deckRow = _deckRow
