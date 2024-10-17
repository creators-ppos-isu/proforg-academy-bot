# @dp.message_handler(state=Form.feedback)
# async def resend_feedback(message: types.Message, state: FSMContext):
#     await message.answer("Спасибо за обратную связь 😉")
#     uid, name, curator_id = sql.select(
#         f"SELECT user_id, name, curator_id FROM user WHERE user_id={message.from_user.id}"
#     )
#     await bot.send_message(curator_id, f"Отзыв от {name} UID: {uid}:\n\n{message.text}")
#     logger.info(f"Feedback from {uid} {name}")
#     await state.finish()


# @dp.message_handler(
#     lambda message: message.from_user.id == settings.OWNER,
#     commands=["feedback"],
# )
# async def do_request(message: types.Message):
# user = sql.select(f"SELECT id FROM user", 0)
# buttons = [{"text": "Отправить отзыв", "callback": "send_feedback"}]
# for user in user:
#     try:
#         await bot.send_message(
#             user[0],
#             "Лекция закончилась! Нажми на кнопку ниже, если хочешь оставить комментарий 👇",
#             reply_markup=modules.markup.inline(buttons),
#         )
#     except Exception as e:
#         logger.error(f"UID: {user[0]} message: {e}")
# logger.warning("Send feedback to each user")