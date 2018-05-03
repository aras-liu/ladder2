import datetime

from ladder.dao.include import *
from ladder.lib.Logger import Logger

logger = Logger("task").getlog()


def addUser(data):
    settle_dt = datetime.datetime.now().strftime('%Y%m%d')
    data.update(settle_dt=settle_dt)

    user = User()
    user_dao = UserDao()
    count = user_dao.countUserDB(settle_dt)
    user_id = "%s%04d" % (settle_dt, int(count) + 1)
    data.update(user_id=user_id)
    user.setUser(data)

    user_dao.insertUser2DB(user)

    return user_id


def openAccount(user_id):
    balance_dao = BalanceDao()
    balance = Balance()
    data = {}
    data.update(user_id=user_id)
    balance.setBalanceDict(data)
    balance_dao.insertBalance2DB(balance)


def register(data):
    """
    register a member
    :param data: save the user information
    :return:
    """
    user_id = addUser(data)
    openAccount(user_id)
    logger.info(" register success !! ")


def addTrans(user_id, trans_at, trans_day, trans_cd):
    """
    add a new trans item
    :param user_id: 用户号
    :param trans_at: 交易金额
    :param trans_day: 交易时间
    :param trans_cd: 交易类型
    :return:
    """
    data_trans = {}

    settle_dt = datetime.datetime.now().strftime('%Y%m%d')
    buss_no = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')

    data_trans.update(user_id=user_id)
    data_trans.update(trans_day=trans_day)
    data_trans.update(trans_at=trans_at)
    data_trans.update(trans_cd=trans_cd)
    data_trans.update(settle_dt=settle_dt)
    data_trans.update(buss_no=buss_no)

    trans = Trans()
    trans_dao = TransDao()
    balance = Balance()
    balance_dao = BalanceDao()
    user_dao=UserDao()

    ret = balance_dao.getBalance(user_id)
    if ret.getCode() != SUCCESS.getCode():
        logger.error("non exist user_id={}".format(user_id))
        return FAILURE.setRet(msg="non exist user_id={}".format(user_id))

    change_balance = {}
    change_balance["current_day"] = int(ret.data["current_day"]) + int(trans_day)
    change_balance["total_day"] = int(ret.data["total_day"]) + int(trans_day)
    change_balance["total_balance"] = int(ret.data["total_balance"]) + int(trans_at)

    curr_day = change_balance["current_day"]
    curr_balance = change_balance["total_balance"]

    data_trans.update(curr_day=curr_day)
    data_trans.update(curr_balance=curr_balance)
    trans.setTrans(data_trans)
    ret = trans_dao.insertTrans(trans)
    if ret.getCode() != SUCCESS.getCode():
        logger.error("non exist user_id={}".format(user_id))
        return FAILURE.setRet(data="non exist user_id={}".format(user_id))

    ret=user_dao.updateUserAttr("user_status","1",user_id)
    logger.info("change_balance={}".format(change_balance))
    return SUCCESS.setData(change_balance)


def chargeAccount(user_id, trans_at, trans_day, trans_cd):

    trans = Trans()
    trans_dao = TransDao()
    balance = Balance()
    balance_dao = BalanceDao()

    ret = addTrans(user_id, trans_at, trans_day, trans_cd)
    if ret.getCode() != SUCCESS.getCode():
        logger.error("add trans Filed user_id={}".format(user_id))
        return FAILURE.setRet(msg="add trans Filed user_id={}".format(user_id))
    logger.info("user_id={} add trans success".format(user_id))
    # balance.setBalanceDict(change_balance)
    # print("ret.data={}".format(ret.data))
    ret = balance_dao.updateBalance(user_id, ret.data)
    if ret.getCode() != SUCCESS.getCode():
        logger.error("update Balance Failed user_id={},che xiao charu Trans".format(user_id))
        trans_at = 0 - int(trans_at)
        trans_day = 0 - int(trans_day)
        trans_cd = "2003"
        ret = addTrans(user_id, trans_at, trans_day, trans_cd)
        if ret.getCode() != SUCCESS.getCode():
            logger.error(" user_id={} rollback failed".format(user_id))
            return FAILURE.setRet(msg=" user_id={} rollback failed".format(user_id))

        logger.error("user_id={},rollback success".format(user_id))
        return FAILURE.setRet(msg="user_id={},rollback success".format(user_id))

    logger.info("charge user_id={} success".format(user_id))


def autoDecreaseDay():
    balance_dao = BalanceDao()
    res = balance_dao.selectBalance("user_id", {})
    user_id_list = [r[0] for r in res]
    print(user_id_list)
    for user_id in user_id_list:
        print(decreaseDay(user_id))


def decreaseDay(user_id):
    # balance = Balance()
    balance_dao = BalanceDao()
    data = {}
    data.update(user_id=user_id)
    res = balance_dao.selectBalance("user_id,current_day,over_day", data)
    user_id = res[0][0]
    current_day = int(res[0][1])
    over_day = int(res[0][2])
    print("current_day={},over_day={}".format(current_day,over_day))
    if current_day + over_day <= 0:
        return "user_id={} stay".format(user_id)
    data_decrease = {"current_day": current_day - 1}
    balance_dao.updateBalance(user_id, data_decrease)

    return "user_id={} change".format(user_id)


def allCharge():
    balance = Balance()
    balance_dao = BalanceDao()

    trans_at = 10
    trans_day = 30
    trans_cd = "2001"

    res = balance_dao.selectBalance("user_id", {})
    user_id_list = [r[0] for r in res]

    res = [chargeAccount(user_id, trans_at, trans_day, trans_cd) for user_id in user_id_list]
    print(res)

def flushTblUser(user_id):
    balance_dao = BalanceDao()
    data = {}
    data.update(user_id=user_id)
    res = balance_dao.selectBalance("user_id,current_day,over_day", data)
    user_id = res[0][0]
    current_day = int(res[0][1])
    over_day = int(res[0][2])
    print("current_day={},over_day={}".format(current_day, over_day))
    if current_day + over_day > 0:
        return "user_id={} stay not change table user".format(user_id)
    ######## ke you hua TODO
    user_dao=UserDao()
    user_dao.updateUserAttr("user_status","0",user_id)

    return "user_id={} stop ".format(user_id)


if __name__ == "__main__":
    # data={}
    # for i in range(50):
    #     qq_no="800000%04d"%(i+100)
    #     qq_name="%04d_test"%(i+100)
    #     data.update(qq_no=qq_no)
    #     data.update(qq_name=qq_name)
    #     register(data)

    # user_id = "201805020002"
    # trans_at = 10
    # trans_day = 30
    # trans_cd="2001"
    #
    # chargeAccount(user_id, trans_at, trans_day,trans_cd)

    # allCharge()
    ##################
    # for i in range(40):
    #     decreaseDay("201805030001")

    ##auto decrease everyday
    autoDecreaseDay()
