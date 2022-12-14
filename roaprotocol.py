from enum import Enum, verify, CONTINUOUS


class ROAPMessageType(Enum):
    OFFER = 'OFFER'
    ANSWER = 'ANSWER'
    OK = 'OK'
    ERROR = 'ERROR'
    SHUTDOWN = 'SHUTDOWN'


class ROAPMessageErrorType(Enum):
    NOMATCH = 'NOMATCH'
    TIMEOUT = 'TIMEOUT'
    REFUSED = 'REFUSED'
    CONFLICT = 'CONFLICT'
    DOUBLECONFLICT = "DOUBLECONFLICT"
    FAILED = 'FAILED'


@verify(CONTINUOUS)
class ROAPSessionStateType(Enum):
    SETUP = 1
    WAITFORCLOSE = 2
    CLOSED = 3


class ROAPSession(object):
    def __init__(self, offer, answer, sid):
        self.state = ROAPSessionStateType.SETUP
        self.offererSessionId = offer
        self.answererSessionId = answer
        self.socketioSid = sid

    def set_state_as_wait_close(self):
        self.state = ROAPSessionStateType.WAITFORCLOSE

    def is_wait_for_close(self):
        return self.state == ROAPSessionStateType.WAITFORCLOSE


class ROAPSessionsManager(object):
    def __init__(self):
        self.allSessions = dict()
        self.allOffererSessionIds = set()
        self.allAnswererSessionIds = set()

    def add_offer(self, offer):
        if offer in self.allOffererSessionIds:
            return False
        else:
            self.allOffererSessionIds.add(offer)
            return True

    def add_answer(self, answer, session):
        if answer in self.allAnswererSessionIds:
            return False
        else:
            self.allAnswererSessionIds.add(answer)
            self.allSessions[answer] = session
            return True

    def get_session_of_answer(self, answer):
        return self.allSessions[answer]

    def is_have_offer(self, offer):
        return offer in self.allOffererSessionIds

    def is_have_answer(self, answer):
        return answer in self.allAnswererSessionIds

    def delete_offer(self, offer):
        self.allOffererSessionIds.remove(offer)

    def delete_answer(self, answer):
        self.allAnswererSessionIds.remove(answer)
        del self.allSessions[answer]

    def delete_offer_and_answer(self, offer, answer):
        self.allOffererSessionIds.remove(offer)
        self.allAnswererSessionIds.remove(answer)
        del self.allSessions[answer]

    def delete_session(self, sid):
        for s in self.allSessions.values():
            if s.socketioSid == sid:
                self.delete_offer_and_answer(
                    s.offererSessionId,
                    s.answererSessionId)
