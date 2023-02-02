import multiprocessing
from enum import Enum, verify, CONTINUOUS


@verify(CONTINUOUS)
class ROAPSessionStateType(Enum):
    SETUP = 1
    WAITFORCLOSE = 2
    CLOSED = 3


class ROAPSession(object):
    def __init__(self):
        self.state = ROAPSessionStateType.SETUP
        self.socketioSid = None
        self.offererSessionId = None
        self.answererSessionId = None

    def set_offer(self, offer):
        self.offererSessionId = offer

    def set_answer(self, answer, sid):
        self.answererSessionId = answer
        self.socketioSid = sid

    def set_state_as_wait_close(self):
        self.state = ROAPSessionStateType.WAITFORCLOSE

    def is_wait_for_close(self):
        return self.state == ROAPSessionStateType.WAITFORCLOSE


class ROAPSessionsManager(object):
    def __init__(self):
        self.mutex = multiprocessing.Manager().Lock()
        self.allSessions = dict()
        self.allOffererSessionIds = set()
        self.allAnswererSessionIds = set()

    def add_offer(self, offer: str):
        self.mutex.acquire()
        if offer in self.allOffererSessionIds:
            self.mutex.release()
            return False
        else:
            s = ROAPSession()
            s.set_offer(offer)
            self.allOffererSessionIds.add(offer)
            self.allSessions[offer] = s
            self.mutex.release()
            return True

    def add_answer(self, offer: str, answer: str, sid: str):
        self.mutex.acquire()
        if answer in self.allAnswererSessionIds:
            self.mutex.release()
            return False
        else:
            s = self.allSessions[offer]
            s.set_answer(answer, sid)
            self.allAnswererSessionIds.add(answer)
            self.mutex.release()
            return True

    def get_session_of_offer(self, offer: str) -> ROAPSession:
        return self.allSessions[offer]

    def is_have_offer(self, offer: str):
        self.mutex.acquire()
        if offer in self.allOffererSessionIds:
            self.mutex.release()
            return True
        else:
            self.mutex.release()
            return False

    def is_have_answer(self, answer: str):
        self.mutex.acquire()
        if answer in self.allAnswererSessionIds:
            self.mutex.release()
            return True
        else:
            self.mutex.release()
            return False

    def delete_offer(self, offer: str):
        self.mutex.acquire()
        self.allOffererSessionIds.remove(offer)
        del self.allSessions[offer]
        self.mutex.release()

    def delete_answer(self, answer: str):
        self.mutex.acquire()
        self.allAnswererSessionIds.remove(answer)
        self.mutex.release()

    def delete_offer_and_answer(self, offer: str, answer: str):
        self.mutex.acquire()
        self.allOffererSessionIds.remove(offer)
        self.allAnswererSessionIds.remove(answer)
        del self.allSessions[offer]
        self.mutex.release()

    def delete_session(self, sid: str):
        self.mutex.acquire()
        for s in self.allSessions.values():
            if s.socketioSid == sid:
                offerer = s.offererSessionId
                answerer = s.answererSessionId
                self.allOffererSessionIds.remove(offerer)
                self.allAnswererSessionIds.remove(answerer)
                del self.allSessions[offerer]
                break
        self.mutex.release()
