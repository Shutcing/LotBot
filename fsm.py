from aiogram.fsm.state import StatesGroup, State

class NewChannelState(StatesGroup):
    new_channel = State()

class NewLotState(StatesGroup):
    new_lot = State()

class ParticipationButtonTitleState(StatesGroup):
    participation_button_title = State()

class RequiredChannelState(StatesGroup):
    required_channel = State()

class WinnersCountState(StatesGroup):
    winners_count = State()

class LotDateState(StatesGroup):
    lot_date = State()

class LotEndDateState(StatesGroup):
    lot_end_date = State()

class LotEndCountState(StatesGroup):
    lot_end_count = State()