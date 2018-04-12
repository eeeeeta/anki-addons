from aqt.reviewer import Reviewer
from aqt.utils import downArrow, tooltip
from anki.utils import stripHTML
from aqt.qt import *
import HTMLParser
def _keyHandlerPatched(self, evt):
    key = unicode(evt.text())
    if self.typedAnswer != None and (key == " " or evt.key() in (Qt.Key_Return, Qt.Key_Enter)):
        cor = stripHTML(self.mw.col.media.strip(self.typeCorrect))
        # ensure we don't chomp multiple whitespace
        cor = cor.replace(" ", "&nbsp;")
        cor = HTMLParser.HTMLParser().unescape(cor)
        cor = cor.replace(u"\xa0", " ")
        if cor == self.typedAnswer:
            self._answerCard(self._defaultEase())
        else:
            tooltip("Typing incorrect: please manually specify difficulty.")
    else:
        normalHandler(self, evt)

def _bottomHTMLNew(self):
        return """
<table width=100%% cellspacing=0 cellpadding=0>
<tr>
<td align=left width=50 valign=top class=stat>
<br>
<button title="%(editkey)s" onclick="py.link('edit');">%(edit)s</button></td>
<td align=center valign=top id=middle>
</td>
<td width=50 align=right valign=top class=stat><span id=time class=stattxt>
</span><br>
<button onclick="py.link('more');">%(more)s %(downArrow)s</button>
</td>
</tr>
</table>
<script>
var time = %(time)d;
var maxTime = 0;
$(function () {
$("#ansbut").focus();
updateTime();
setInterval(function () { time += 1; updateTime() }, 1000);
});
var updateTime = function () {
    if (!maxTime) {
        $("#time").text("");
        return;
    }
    time = Math.min(maxTime, time);
    var m = Math.floor(time / 60);
    var s = time %% 60;
    if (s < 10) {
        s = "0" + s;
    }
    var e = $("#time");
    if (maxTime == time) {
        e.html("<font color=red>" + m + ":" + s + "</font>");
    } else {
        e.text(m + ":" + s);
    }
}
function showQuestion(txt, maxTime_) {
  // much faster than jquery's .html()
  $("#middle")[0].innerHTML = txt;
  $("#ansbut").focus();
  time = 0;
  maxTime = maxTime_;
}
function showAnswer(txt) {
  $("#middle")[0].innerHTML = txt;

}
</script>
""" % dict(rem=self._remaining(), edit=_("Edit"),
           editkey=_("Shortcut key: %s") % "E",
           more=_("More"),
           downArrow=downArrow(),
           time=self.card.timeTaken() // 1000)


normalHandler = Reviewer._keyHandler
Reviewer._keyHandler = _keyHandlerPatched
Reviewer._bottomHTML = _bottomHTMLNew
