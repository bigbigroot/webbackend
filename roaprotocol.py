import json
from enum import Enum, auto, verify, CONTINUOUS

class ROAPMessageType(Enum):
    Offer = 'OFFER'
    Answer = 'ANSWER'
    Ok = 'OK'
    Error = 'ERROR'
    Shutdown = 'SHUTDOWN'

class ROAPMessageErrorType(Enum):
    NoMatch = 'NOMATCH'
    Timeout = 'TIMEOUT'
    Refused = 'REFUSED'
    Conflict = 'CONFLICT'
    DoubleConflict = "DOUBLECONFLICT"
    Failed = 'FAILED'

@verify(CONTINUOUS)
class ROAPSessionStateType(Enum):
    Setup = 1
    WaitForClose = 4
    Closed = 5

class ROAPSession():
    def __init__(self, offer, answer, sid):
        self.state = ROAPSessionStateType.Setup
        self.offererSessionId = offer
        self.answererSessionId = answer
        self.socketioSid = sid
    def setStateWaitClose(self):
        self.state = ROAPSessionStateType.WaitForClose
    
    def isWaitClose(self):
        return self.state == ROAPSessionStateType.WaitForClose

class ROAPSessionsManager():
    def __init__(self):
        self.allSessions : dict
        self.allOffererSessionIds : set
        self.allAnswererSessionIds : set

    def addOffer(self, offer):
        if offer in self.allOffererSessionIds:
            return False
        else:
            self.allOffererSessionIds.add(offer)
            return True

    def addAnswer(self, answer, session):
        if answer in self.allAnswererSessionIds:
            return False
        else:
            self.allAnswererSessionIds.add(answer)
            self.allSessions[answer] = session
            return True

    def getAnswerSession(self, answer):
        return allSessions[answer]

    def isHaveOffer(self, offer):
        return offer in self.allOffererSessionIds

    def isHaveAnswer(self, answer):
        return answer in self.allAnswererSessionIds
    
    def deleteOffer(self, offer):
        self.allOffererSessionIds.remove(offer)

    def deleteAnswer(self, answer):
        self.allAnswererSessionIds.remove(answer)
        del self.allSessions[answer]

    def deleteOfferAndAnswer(self, offer, answer):
        self.allOffererSessionIds.remove(offer)
        self.allAnswererSessionIds.remove(answer)
        del self.allSessions[answer]

    def deleteSession(self, sid):
        for s in self.allSessions.values:
            if s.socketioSid == sid:
                self.deleteOfferAndAnswer(s.offererSessionId, 
                s.answererSessionId)