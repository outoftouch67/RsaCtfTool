#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from attacks.abstract_attack import AbstractAttack
from tqdm import tqdm
from lib.utils import isqrt, invmod
from lib.keys_wrapper import PrivateKey
from lib.utils import timeout, TimeoutError


class Attack(AbstractAttack):
    def __init__(self, attack_rsa_obj, timeout=60):
        super().__init__(attack_rsa_obj, timeout)
        self.speed = AbstractAttack.speed_enum["medium"]

    def close_factor(self, n, b):
        # approximate phi
        phi_approx = n - 2 * isqrt(n) + 1

        # create a look-up table
        look_up = {}
        z = 1
        for i in tqdm(range(0, b + 1)):
            look_up[z] = i
            z = (z * 2) % n

        # check the table
        mu = invmod(pow(2, phi_approx, n), n)
        fac = pow(2, b, n)

        for i in tqdm(range(0, b + 1)):
            if mu in look_up:
                phi = phi_approx + (look_up[mu] - i * b)
                break
            mu = (mu * fac) % n
        else:
            return None

        m = n - phi + 1
        roots = ((m - isqrt(m ** 2 - 4 * n)) // 2, (m + isqrt(m ** 2 - 4 * n)) // 2)

        if roots[0] * roots[1] == n:
            return roots

    def attack(self, publickey, cipher=[]):
        """Do nothing, used for multi-key attacks that succeeded so we just print the
        private key without spending any time factoring
        """
        londahl_b = 20000000
        with timeout(self.timeout):
            try:
                factors = self.close_factor(publickey.n, londahl_b)

                if factors is not None:
                    p, q = factors
                    priv_key = PrivateKey(
                        int(p), int(q), int(publickey.e), int(publickey.n)
                    )
                    return (priv_key, None)
                else:
                    return (None, None)
            except TimeoutError:
                return (None, None)
        return (None, None)

    def test(self):
        from lib.keys_wrapper import PublicKey

        key_data = """-----BEGIN PUBLIC KEY-----
MIGeMA0GCSqGSIb3DQEBAQUAA4GMADCBiAKBgAOBxiQviVpL4G5d0TmVmjDn51zu
iravDlD4vUlVk9XK79/fwptVzYsjimO42+ZW5VmHF2AUXaPhDC3jBaoNIoa78CXO
ft030bR1S0hGcffcDFMm/tZxwu2/AAXCHoLdjHSwL7gxtXulFxbWoWOdSq+qxtak
zBSZ7R1QlDmbnpwdAgMDEzc=
-----END PUBLIC KEY-----"""
        self.timeout = 120
        result = self.attack(PublicKey(key_data))
        return result != (None, None)
