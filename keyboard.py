import time
import extronlib
from extronlib import event
import string

debug = False
if not debug:
    print = lambda *a, **k: None


class Keyboard:
    '''
        An object that manages the keyboard buttons.
        If a keyboard button is pressed, self.string will be updated accordingly.

        This will allow the programmer to copy/paste the keyboard GUI page into their GUID project without worrying about the __KeyIDs
        '''

    def __init__(self,
                 TLP=None,
                 KeyIDs=None,
                 BackspaceID=None,
                 ClearID=None,
                 FeedbackObject=None,
                 SpaceBarID=None,
                 ShiftID=None,
                 SymbolID=None
                 ):
        print('Keyboard object initializing')

        self.TLP = TLP
        self.__KeyIDs = KeyIDs if KeyIDs is not None else []
        self.__KeyButtons = []
        self.ShiftID = ShiftID

        self.__SymbolID = SymbolID
        self.__allSymbols = []
        self.__symbolMode = False

        self.FeedbackObject = FeedbackObject

        self.TextFields = {}  # Format: {FeedbackObject : 'Text'}, this keeps track of the text on various Label objects.

        self.bDelete = extronlib.ui.Button(TLP, BackspaceID, holdTime=0.2, repeatTime=0.1)

        self.string = ''

        self.CapsLock = True  # default caps lock setting at boot-up
        self.ShiftMode = 'Upper'
        self._password_mode = False
        self._stringChangesCallback = None
        self._keyPressedCallback = None
        self._keyPressedCallbackEnable = True

        # Clear Key
        if ClearID is not None:
            self.bClear = extronlib.ui.Button(TLP, ClearID)

            @event(self.bClear, 'Pressed')
            def clearPressed(button, state):
                print('57 clearPressed(', button, state)
                self.ClearString()
        else:
            self.bClear = None

        # Delete key
        @event(self.bDelete, 'Pressed')
        @event(self.bDelete, 'Tapped')
        @event(self.bDelete, 'Repeated')
        @event(self.bDelete, 'Released')
        def deletePressed(button, state):
            # print(button.Name, state)
            if state == 'Pressed':
                button.SetState(1)

            elif state in ['Tapped', 'Released']:
                button.SetState(0)

            if state in ['Pressed', 'Repeated']:
                self.DeleteCharacter()
                self._KeyPressed('backspace')

        # Spacebar

        if SpaceBarID is not None:
            @event(extronlib.ui.Button(TLP, SpaceBarID), ['Pressed', 'Released'])
            def SpacePressed(button, state):
                # print(button.Name, state)
                if state == 'Pressed':
                    button.SetState(1)
                elif state == 'Released':
                    button.SetState(0)

                    self.AppendToString(' ')

        # Character Keys
        def CharacterPressed(button, state):
            # print(button.Name, state)
            # print('Before self.CapsLock=', self.CapsLock)
            # print('Before self.ShiftMode=', self.ShiftMode)

            if state == 'Pressed':
                button.SetState(1)
                Char = button.Name
                if Char is not None:
                    if ShiftID is not None:
                        if self.__symbolMode is True:
                            Char = self.__GetButtonSymbol(button)
                        else:
                            if self.ShiftMode == 'Upper':
                                Char = Char.upper()
                            else:
                                Char = Char.lower()

                    self.AppendToString(Char)

            elif state == 'Released':
                if self.CapsLock is False:
                    if self.__symbolMode is False:
                        if self.ShiftMode == 'Upper':
                            self.ShiftMode = 'Lower'
                            self.updateKeysShiftMode()

                button.SetState(0)

                # print('After self.CapsLock=', self.CapsLock)
                # print('After self.ShiftMode=', self.ShiftMode)

        for ID in KeyIDs:
            NewButton = extronlib.ui.Button(TLP, ID)
            NewButton.Pressed = CharacterPressed
            NewButton.Released = CharacterPressed
            self.__KeyButtons.append(NewButton)

        # Shift Key
        if ShiftID is not None:
            self.ShiftKey = extronlib.ui.Button(TLP, ShiftID, holdTime=1)

            @event(self.ShiftKey, 'Pressed')
            @event(self.ShiftKey, 'Tapped')
            @event(self.ShiftKey, 'Held')
            @event(self.ShiftKey, 'Released')
            def ShiftKeyEvent(button, state):
                # print(button.Name, state)
                # print('Before self.CapsLock=', self.CapsLock)
                # print('Before self.ShiftMode=', self.ShiftMode)

                self.__symbolMode = False
                self.__SymbolButton.SetState(0)

                if state == 'Pressed':
                    button.SetState(1)
                    time.sleep(0.1)
                    button.SetState(0)

                elif state == 'Tapped':
                    if self.CapsLock is True:
                        self.CapsLock = False
                        self.ShiftMode = 'Lower'

                    elif self.CapsLock is False:
                        if self.ShiftMode == 'Upper':
                            self.ShiftMode = 'Lower'

                        elif self.ShiftMode == 'Lower':
                            self.ShiftMode = 'Upper'

                    self.updateKeysShiftMode()

                elif state == 'Held':
                    self.CapsLock = not self.CapsLock

                    if self.CapsLock == True:
                        self.ShiftMode = 'Upper'

                    elif self.CapsLock == False:
                        self.ShiftMode = 'Lower'

                    self.updateKeysShiftMode()

                    # print('After self.CapsLock=', self.CapsLock)
                    # print('After self.ShiftMode=', self.ShiftMode)

            self.updateKeysShiftMode()

        if self.__SymbolID is not None:
            for i in range(10):
                self.__allSymbols.append(str(i))
            self.__allSymbols.extend([chr(i) for i in range(33, 47 + 1)])
            self.__allSymbols.extend([chr(i) for i in range(58, 64 + 1)])
            self.__allSymbols.extend([chr(i) for i in range(91, 96 + 1)])
            self.__allSymbols.extend([chr(i) for i in range(123, 126 + 1)])

            self.__SymbolButton = extronlib.ui.Button(TLP, self.__SymbolID)

            @event(self.__SymbolButton, 'Pressed')
            def SymbolButtonEvent(button, state):

                self.__symbolMode = not self.__symbolMode
                button.SetState(int(self.__symbolMode))
                self._SetSymbols()

    def SetSymbolMode(self, state):
        self.__symbolMode = bool(state)
        if self.__SymbolButton:
            self.__SymbolButton.SetState(int(self.__symbolMode))
        self._SetSymbols()

    def _SetSymbols(self):

        if self.__symbolMode:
            print('going into symbol mode')
            for btn in self.__KeyButtons:
                btn.SetText(self.__GetButtonSymbol(btn))
        else:
            print('coming out of symbol mode, to alpha mode')
            for btn in self.__KeyButtons:

                if btn.Name is None:
                    print('206 btn.ID=', btn.ID)

                if btn.Name.isalpha():
                    if self.ShiftMode == 'Upper' or self.CapsLock:
                        btn.SetText(btn.Name.upper())
                    else:
                        btn.SetText(btn.Name.lower())
                else:  # except Exception as e:
                    # print('205 Keyboard Exception:', e, ', button.ID=', btn.ID)
                    btn.SetText(btn.Name)

        self._updateLabel()

    def _KeyPressed(self, key):
        '''

        :param key: str; should be on of these possible values: https://pyautogui.readthedocs.io/en/latest/keyboard.html
        :return:
        '''
        if self._keyPressedCallback and self._keyPressedCallbackEnable:
            self._keyPressedCallback(self, key)

    def __GetButtonSymbol(self, btn):
        index = self.__KeyButtons.index(btn)
        index = index - len(self.__allSymbols)
        return self.__allSymbols[index]

    def updateKeysShiftMode(self):
        if self.ShiftID is not None:
            if self.ShiftMode == 'Upper':
                self.ShiftKey.SetState(1)

            elif self.ShiftMode == 'Lower':
                self.ShiftKey.SetState(0)

            for button in self.__KeyButtons:
                Char = button.Name
                # print('Keyboard.updateKeysShiftMode Char=', Char)
                if Char:
                    if self.ShiftID is not None:
                        if self.ShiftMode == 'Upper':
                            Char = Char.upper()
                        else:
                            Char = Char.lower()
                        button.SetText(Char)

    # Define the class methods
    def GetString(self):
        '''
        return the value of the keyboard buffer
        '''
        # print('Keyboard.GetString()=',self.string)
        return self.string

    def SetString(self, s):
        self.string = s
        self._updateLabel()
        self._DoStringChangesCallback()

    def ClearString(self):
        '''
        clear the keyboard buffer
        '''
        # print('Keyboard.ClearString()')
        self.string = ''
        self.ShiftID = 'Upper'
        self._updateLabel()
        self._DoStringChangesCallback()

    def AppendToString(self, character=''):
        '''
        Add a character(s) to the string
        '''
        # print('Keyboard.AppendToString()')
        self.string += character
        self._updateLabel()
        self._DoStringChangesCallback()
        self._KeyPressed(character)

    def DeleteCharacter(self):
        '''
        Removes one character from the end of the string.
        '''
        # print('deleteCharacter before=',self.string)
        self.string = self.string[0:len(self.string) - 1]
        print('deleteCharacter after=', self.string)
        self._updateLabel()
        self._DoStringChangesCallback()

    def _updateLabel(self):
        '''
        Updates the TLP label with the current self.string
        '''
        # print('updateLabel()')
        if self._password_mode:
            pw_string = ''
            for ch in self.GetString():
                pw_string += '*'
            if self.FeedbackObject:
                self.FeedbackObject.SetText(pw_string)
        else:
            if self.FeedbackObject:
                self.FeedbackObject.SetText(self.GetString())
                # print('self.FeedbackObject=', self.FeedbackObject)

        if self.bClear is not None:
            if len(self.GetString()) == 0:
                if self.bClear.Visible:
                    self.bClear.SetVisible(False)
            else:
                if not self.bClear.Visible:
                    self.bClear.SetVisible(True)

    def SetFeedbackObject(self, NewFeedbackObject):
        '''
        Changes the ID of the object to receive feedback.
        This class will remember the text that should be applied to each feedback object.
        Allowing the user/programmer to switch which field the keyboard is modifiying, on the fly.
        '''
        # Save the current text
        self.TextFields[self.FeedbackObject] = self.GetString()

        # Load new text (if available)
        try:
            self.string = self.TextFields[NewFeedbackObject]
        except:
            self.string = ''

        # Update the TLP
        self.FeedbackObject = NewFeedbackObject
        self._updateLabel()
        self._DoStringChangesCallback()

    def GetFeedbackObject(self):
        return self.FeedbackObject

    def SetPasswordMode(self, mode):
        # mode = bool
        self._password_mode = mode

    def _DoStringChangesCallback(self):
        if callable(self._stringChangesCallback):
            self._stringChangesCallback(self, self.GetString())

    @property
    def StringChanges(self):
        return self._stringChangesCallback

    @StringChanges.setter
    def StringChanges(self, func):
        self._stringChangesCallback = func

    @property
    def KeyPressed(self):
        return self._keyPressedCallback

    @KeyPressed.setter
    def KeyPressed(self, func):
        self._keyPressedCallback = func

    def EnableKeyPressedCallback(self, state):
        self._keyPressedCallbackEnable = state

    @property
    def PasswordMode(self):
        return self._password_mode
