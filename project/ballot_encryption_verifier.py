from project import json_parser
from project.contest_verifier import BallotContestVerifier
from project.vote_limit_counter import VoteLimitCounter


class BallotEncryptionVerifier:
    """
    This class checks ballot correctness on each ballot. Ballot correctness can be represented by:
    1. correct encryption (of value 0 or 1) of each selection within each contest (box 3)
    2. selection limits are satisfied for each contest (box 4)
    """

    def __init__(self, ballot_dic: dict, generator: int, public_key: int, extended_hash: int, vote_limit_dic: dict):
        """"""
        self.ballot_dic = ballot_dic
        self.generator = generator
        self.public_key = public_key
        self.extended_hash = extended_hash
        self.vote_limit_dic = vote_limit_dic

    def verify_all_contests(self) -> bool:
        """
        verify all the contests within a ballot
        :return: True if all contests checked out/no error, False if any error in any selection
        """
        error = False

        ballot_id = self.ballot_dic.get('object_id')
        contests = self.ballot_dic.get('contests')

        for contest in contests:
            cv = BallotContestVerifier(contest, self.generator, self.public_key,
                                       self.extended_hash, self.vote_limit_dic)
            res = cv.verify_a_contest()
            if not res:
                error = True

        if not error:
            print(ballot_id + ' ballot correctness verification success.')
        else:
            print(ballot_id + ' ballot correctness verification failure.')

        return not error





# TODO: do unit test
if __name__ == '__main__':
    constants_d = json_parser.read_json_file('/Users/rainbowhuang/Desktop/ElectionGuard/data_08132020/constants.json')
    context_d = json_parser.read_json_file('/Users/rainbowhuang/Desktop/ElectionGuard/data_08042020/context.json')
    ballot_d = json_parser.read_json_file('/Users/rainbowhuang/Desktop/ElectionGuard/data_08042020/encrypted_ballots'
                                          '/ballot_ballot-ce63b0b0-d67c-11ea-8412-acde48001122.json')
    description_dic = json_parser.read_json_file(
        '/Users/rainbowhuang/Desktop/ElectionGuard/data_08132020/description.json')

    g = int(constants_d.get('generator'))
    pk = int(context_d.get('elgamal_public_key'))
    ehash = int(context_d.get('crypto_extended_base_hash'))

    vlc = VoteLimitCounter(description_dic)
    vote_limit_d = vlc.get_contest_vote_limits()

    bv = BallotEncryptionVerifier(ballot_d, g, pk, ehash, vote_limit_d)
    bv.verify_all_contests()