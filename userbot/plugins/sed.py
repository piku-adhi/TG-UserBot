# TG-UserBot - A modular Telegram UserBot script for Python.
# Copyright (C) 2019  Kandarp <https://github.com/kandnub>
#
# TG-UserBot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TG-UserBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TG-UserBot.  If not, see <https://www.gnu.org/licenses/>.


# This is based on https://github.com/SijmenSchoon/regexbot
# but slightly different.
# https://stackoverflow.com/a/46100580 is also very helpful with the
# explanation on how we could make it work and what we'd need to check.


import asyncio
import os
import re

from userbot import client
from userbot.helper_funcs.sed import sub_matches
from userbot.utils.events import NewMessage


pattern = (
    r'(?:^|;.+?)'  # Ensure that the expression doesn't go blatant
    r'([1-9]+?)?'  # line: Don't match a 0, sed counts lines from 1
    r'(?:sed|s)'  # The s command (as in substitute)
    r'(?:(?P<d>.))'  # Unknown delimiter with a named group d
    r'((?:(?!(?<![^\\]\\)(?P=d)).)+)'  # regexp
    r'(?P=d)'  # Unknown delimiter
    r'((?:(?!(?<![^\\]\\)(?P=d)|(?<![^\\]\\);).)*)'  # replacement
    r'(?:(?=(?P=d)|;).)?'  # Check if it's a delimiter or a semicolon
    r'((?<!;)\w+)?'  # flags: Don't capture if it starts with a semicolon
    r'(?=;|$)'  # Ensure it ends with a semicolon for the next match
)
ub_sed_pattern = r"^(?:[1-9]+sed|[1-9]+s|sed)"


@client.onMessage(
    command="sed", outgoing=True, disable_prefix=True,
    regex=(pattern, re.MULTILINE | re.IGNORECASE | re.DOTALL)
)
async def sed_substitute(event: NewMessage.Event) -> None:
    """Perfom a GNU like SED substitution of the matched text."""
    if not re.match(ub_sed_pattern, event.raw_text, re.IGNORECASE):
        return

    matches = event.matches
    reply = await event.get_reply_message()

    try:
        if reply:
            original = reply
            if not original:
                return

            newStr = await sub_matches(matches, original.raw_text)
            if newStr:
                await original.reply('[SED]\n\n' + newStr)
        else:
            total_messages = []  # Append messages to avoid timeouts
            count = 0  # Don't fetch more than ten texts/captions

            async for msg in client.iter_messages(
                event.chat_id,
                offset_id=event.message.id
            ):
                if msg.raw_text:
                    total_messages.append(msg)
                    count += 1
                else:
                    continue
                if count >= 10:
                    break

            for message in total_messages:
                newStr = await sub_matches(matches, message.raw_text)
                if newStr:
                    await message.reply('[SED]\n\n' + newStr)
                    break
    except Exception as e:
        await event.answer((
            f"{event.raw_text}"
            '\n\n'
            'Like regexbox says, fuck me.\n'
            '`'
            f"{str(type(e))}"
            ':` `'
            f"{str(e)}"
            '`'
        ), reply=True)


@client.onMessage(
    command="regexninja",
    outgoing=True, regex=r"regexninja(?: |$)(on|off)?$"
)
async def regex_ninja(event: NewMessage.Event) -> None:
    """Enable and disable ninja mode for @regexbot"""
    arg = event.matches[0].group(1)
    ninja = os.environ.get("userbot_regexninja", False)

    if not arg:
        if ninja:
            await event.answer("`Regex ninja is enabled.`")
        else:
            await event.answer("`Regex ninja is disabled.`")
        return

    if arg == "on":
        os.environ["userbot_regexninja"] = "True"
        value = "enabled"
    else:
        del os.environ["userbot_regexninja"]
        value = "disabled"

    await event.answer(
        f"`Successfully {value} ninja mode for @regexbot!`",
        log=("regexninja", f"{value.title()} ninja mode for @regexbot!")
    )
    await asyncio.sleep(2)
    await event.delete()


@client.onMessage(
    outgoing=True, disable_prefix=True,
    regex=(r'^s/((?:\\/|[^/])+)/((?:\\/|[^/])*)(/.*)?', re.IGNORECASE)
)
async def ninja(event: NewMessage.Event) -> None:
    """Deletes our sed messages if regexninja is enabled"""
    ninja = os.environ.get("userbot_regexninja", False)
    if ninja:
        await asyncio.sleep(0.5)
        await event.delete()
