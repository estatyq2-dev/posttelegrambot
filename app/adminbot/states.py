"""FSM states for admin bot."""

from aiogram.fsm.state import State, StatesGroup


class AddChannelStates(StatesGroup):
    """States for adding a channel."""
    waiting_for_forward = State()


class AddSourceStates(StatesGroup):
    """States for adding a source."""
    waiting_for_type = State()
    waiting_for_handle = State()
    waiting_for_url = State()


class EditChannelStates(StatesGroup):
    """States for editing channel settings."""
    selecting_channel = State()
    selecting_setting = State()
    waiting_for_interval = State()
    waiting_for_language = State()
    waiting_for_style = State()


class EditSourceStates(StatesGroup):
    """States for editing source settings."""
    selecting_source = State()
    selecting_setting = State()
    waiting_for_interval = State()


class BindingStates(StatesGroup):
    """States for creating bindings."""
    selecting_source = State()
    selecting_channel = State()


class DeleteStates(StatesGroup):
    """States for deleting items."""
    confirming_channel = State()
    confirming_source = State()
    confirming_binding = State()

