class TestRegistration:
    def test_commands_registered(self, bot):
        import bot.config as config
        expected = {
            'help',
            'owe',
            config.GET_DEBTS_COMMAND,
            config.GET_ALL_DEBTS_COMMAND,
            config.DEBTS_WITH_USER_COMMAND,
            'transactions',
            'settle',
            'cashout',
            'set_unicode_preference',
            'refresh_name',
            config.ROLL_COMMAND,
            'settings',
        }
        assert set(bot.tree.commands.keys()) == expected
