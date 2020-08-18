from project import constants, hash, number
from project.share_verifier import ShareVerifier

class BallotSelectionVerifier:
    """
    This class is responsible for verify one selection at a time,
    its main purpose is to confirm selection validity,
    will be used in ballot_validity_verifier
    """
    def __init__(self, selection_dic: dict, generator: int, public_key: int, extended_hash: int):
        self.selection_dic = selection_dic
        self.public_key = public_key
        self.generator = generator
        self.extended_hash = extended_hash
        self.pad = int(self.selection_dic.get('ciphertext', {}).get('pad'))
        self.data = int(self.selection_dic.get('ciphertext', {}).get('data'))

        # constants
        self.ZRP_PARAM_NAMES = {'pad', 'data'}
        self.ZQ_PARAM_NAMES = {'challenge', 'response'}

    def get_pad_data(self) -> tuple:
        """
        get a selection's alpha and beta
        :return:
        """
        return self.pad, self.data

    def is_placeholder_selection(self) -> bool:
        """
        check if a selection is a placeholder
        :param selection_dic:
        :return:
        """

        return bool(self.selection_dic.get('is_placeholder_selection'))

    # --------------------------------------- validity check ----------------------------------------------------
    def verify_selection_validity(self) -> bool:
        """
        verify a selection within a contest
        :param selection_dic:
        :return:
        """
        error = False

        # get dictionaries
        cipher_dic = self.selection_dic.get('ciphertext')
        proof_dic = self.selection_dic.get('proof')

        # get values
        pad = int(cipher_dic.get('pad'))  # alpha
        data = int(cipher_dic.get('data'))  # beta

        selection_id = self.selection_dic.get('object_id')
        zero_pad = int(proof_dic.get('proof_zero_pad'))  # a0
        one_pad = int(proof_dic.get('proof_one_pad'))  # a1
        zero_data = int(proof_dic.get('proof_zero_data'))  # b0
        one_data = int(proof_dic.get('proof_one_data'))  # b1
        zero_challenge = int(proof_dic.get('proof_zero_challenge'))  # c0
        one_challenge = int(proof_dic.get('proof_one_challenge'))  # c1
        zero_response = int(proof_dic.get('proof_zero_response'))  # v0
        one_response = int(proof_dic.get('proof_one_response'))  # v1

        # point 1: check alpha, beta, a0, b0, a1, b1 are all in set Zrp
        if not (self.__check_params_within_zrp(cipher_dic) and self.__check_params_within_zrp(proof_dic)):
            error = True

        # point 3: check if the given values, c0, c1, v0, v1 are each in the set zq
        if not self.__check_params_within_zq(proof_dic):
            error = True

        # point 2: conduct hash computation, c = H(Q-bar, (alpha, beta), (a0, b0), (a1, b1))
        challenge = hash.hash_elems(self.extended_hash, pad, data, zero_pad, zero_data, one_pad, one_data)

        # point 4:  c = c0 + c1 mod q is satisfied
        if not self.__check_hash_comp(challenge, zero_challenge, one_challenge):
            error = True

        # point 5: check equations
        if not (self.__check_equation1(pad, zero_pad, zero_challenge, zero_response) and
                self.__check_equation1(pad, one_pad, one_challenge, one_response) and
                self.__check_equation2(data, zero_data, zero_challenge, zero_response) and
                self.__check_equation3(data, one_data, one_challenge, one_response)):
            error = True

        if error:
            print(selection_id + ' validity verification failure.')

        return not error

    def __check_params_within_zrp(self, param_dic: dict) -> bool:
        """
        check if the given values, alpha, beta, a0, b0, a1, b1 are all in set Zrp
        alpha, beta are from cipher dic and the others are from proof_dic
        :param param_dic: either ciphertext_dic or proof_dic generated in __verify_a_selection
        :return: True if all parameters in this given dict are within set zrp
        """
        error = False
        # all the relevant parameters in one loop
        for (k, v) in param_dic.items():
            # if it's a desired field, verify the number
            if any(name in k for name in self.ZRP_PARAM_NAMES):
                res = number.is_within_set_zrp(v)
                if not res:
                    error = True
                    print('parameter error, {name} is not in set Zrp. '.format(name=k))

        return not error

    def __check_params_within_zq(self, param_dic: dict) -> bool:
        """
        check if the given values, c0, c1, v0, v1 are each in the set zq
        :param param_list:
        :return:
        """
        error = False

        for (k, v) in param_dic.items():
            if any(name in k for name in self.ZQ_PARAM_NAMES):
                res = number.is_within_set_zq(v)
                if not res:
                    error = True
                    print('parameter error, {name} is not in set Zq. '.format(name=k))

        return not error

    def __check_equation1(self, pad: int, x_pad: int, x_chal: int, x_res: int) -> bool:
        """

        :param x_pad:
        :param x_chal:
        :param x_res:
        :return:
        """
        equ1_left = pow(self.generator, x_res, constants.LARGE_PRIME)
        equ1_right = number.mod(x_pad * pow(pad, x_chal, constants.LARGE_PRIME), constants.LARGE_PRIME)
        res = number.equals(equ1_left, equ1_right)

        if not res:
            print("equation 1 error. ")

        return res

    def __check_equation2(self, data: int, zero_data: int, zero_chal: int, zero_res: int) -> bool:
        """

        :param data:
        :param zero_data:
        :param zero_chal:
        :param zero_res:
        :return:
        """
        equ2_left = pow(self.public_key, zero_res, constants.LARGE_PRIME)
        equ2_right = number.mod(zero_data * pow(data, zero_chal, constants.LARGE_PRIME), constants.LARGE_PRIME)

        res = number.equals(equ2_left, equ2_right)

        if not res:
            print("equation 2 error. ")

        return res

    def __check_equation3(self, data: int, one_data: int, one_chal: int, one_res: int) -> bool:
        """

        :param data:
        :param one_data:
        :param one_chal:
        :param one_res:
        :return:
        """
        equ3_left = number.mod(pow(self.generator, one_chal, constants.LARGE_PRIME) *
                               pow(self.public_key, one_res, constants.LARGE_PRIME), constants.LARGE_PRIME)
        equ3_right = number.mod(one_data * pow(data, one_chal, constants.LARGE_PRIME), constants.LARGE_PRIME)

        res = number.equals(equ3_left, equ3_right)
        if not res:
            print("equation 3 error. ")

        return res

    def __check_hash_comp(self, chal, zero_chal, one_chal) -> bool:
        """
        check if the equation c = c0 + c1 mod q is satisfied.
        :param chal:
        :param zero_chal:
        :param one_chal:
        :return:
        """
        # calculated expected challenge value: c0 + c1 mod q
        expected = number.mod(int(zero_chal) + int(one_chal),
                              constants.SMALL_PRIME)

        res = number.equals(chal, expected)

        if not res:
            print("challenge value error.")

        return res

    # --------------------------------------- limit check ----------------------------------------------------
    def verify_selection_limit(self):
        """

        :return:
        """
        return self.__check_a_b()

    def __check_a_b(self) -> bool:
        """
        check if a selection's a and b are in set Zrp - box 4, limit check
        :return: True if a and b both within set zrp
        """

        a_res = number.is_within_set_zrp(self.pad)
        b_res = number.is_within_set_zrp(self.data)

        if not a_res:
            print('selection pad/a value error. ')

        if not b_res:
            print('selection data/b value error. ')

        return a_res and b_res

# TODO:
class TallySelectionVerifier:
    def __init__(self, selection_dic: dict, generator: int, extended_hash: int, public_keys: list):
        self.selection_dic = selection_dic
        self.selection_id = selection_dic.get('object_id')
        self.pad = int(self.selection_dic.get('message', {}).get('pad'))
        self.data = int(self.selection_dic.get('message', {}).get('data'))
        self.generator = generator
        self.extended_hash = extended_hash
        self.public_keys = public_keys


    def get_pad_data(self) -> tuple:
        """
        get a selection's alpha and beta
        :return:
        """
        return self.pad, self.data

    def verify_a_selection(self) -> bool:
        """

        :return:
        """
        shares = self.selection_dic.get('shares')
        sv = ShareVerifier(shares, self.pad, self.data, self.generator, self.extended_hash, self.public_keys)
        res = sv.verify_all_shares()
        if not res:
            print(self.selection_id + " tally verification error. ")

        return res