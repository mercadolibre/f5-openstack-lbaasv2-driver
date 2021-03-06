# coding=utf-8
u"""F5 Networks® LBaaSv2 L7 rules client for tempest tests."""
# Copyright 2016 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from tempest import config

from f5.bigip import ManagementRoot

config = config.CONF


class BigIpClient(object):
    def __init__(self):
        self.bigip = ManagementRoot(config.f5_lbaasv2_driver.icontrol_hostname,
                                    config.f5_lbaasv2_driver.icontrol_username,
                                    config.f5_lbaasv2_driver.icontrol_password)

    def folder_exists(self, folder):
        return self.bigip.tm.sys.folders.folder.exists(name=folder)

    def policy_exists(self, name, partition):
        return self.bigip.tm.ltm.policys.policy.exists(
            name=name, partition=partition)

    def rule_exists(self, policy_name, rule_name, partition):
        if self.policy_exists(policy_name, partition):
            policy = self.bigip.tm.ltm.policys.policy.load(
                name=policy_name, partition=partition)
            return policy.rules_s.rules.exists(
                name=rule_name, partition=partition)
        else:
            return False

    def rule_has_action(self, policy_name, rule_name, action, partition):
        if self.rule_exists(policy_name, rule_name, partition):
            policy = self.bigip.tm.ltm.policys.policy.load(
                name=policy_name, partition=partition)
            rule = policy.rules_s.rules.load(name=rule_name)

            if rule.actions_s.actions.exists(name='0'):
                rule_action = rule.actions_s.actions.load(name='0')
                if action == 'REJECT':
                    return getattr(rule_action, 'reset', False)
                elif action == 'REDIRECT_TO_URL':
                    return getattr(rule_action, 'redirect', False)
                elif action == 'REDIRECT_TO_POOL':
                    return getattr(rule_action, 'forward', False)

        return False

    def rule_is_reject(self, policy_name, rule_name, partition):
        return self.rule_has_action(
            policy_name, rule_name, 'REJECT', partition)

    def rule_is_redirect_to_pool(self, policy_name, rule_name, partition):
        return self.rule_has_action(
            policy_name, rule_name, 'REDIRECT_TO_POOL', partition)

    def rule_is_redirect_to_url(self, policy_name, rule_name, partition):
        return self.rule_has_action(
            policy_name, rule_name, 'REDIRECT_TO_URL', partition)

    def rule_conditions(self, policy_name, rule_name, partition):
        if self.rule_exists(policy_name, rule_name, partition):
            policy = self.bigip.tm.ltm.policys.policy.load(
                name=policy_name, partition=partition)
            rule = policy.rules_s.rules.load(name=rule_name)

            return rule.conditions_s.get_collection()
        return []

    def rule_has_condition(
            self, policy_name, rule_name, cond_name, value, partition):
        conditions = self.rule_conditions(policy_name, rule_name, partition)
        for cond in conditions:
            cond_val = getattr(cond, cond_name, None)
            assert len(cond.values) == 1
            value_str = cond.values[0]
            # Condition value should be set to True if condition type is
            # httpHost or condition comparison type is startsWith etc...
            # The values attribute should only contain one value and it
            # should be set to some string, even if it's empty
            if cond_val and value_str == value:
                return True
        return False

    def rule_has_starts_with(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'startsWith', value, partition)

    def rule_has_ends_with(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'endsWith', value, partition)

    def rule_has_contains(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'contains', value, partition)

    def rule_has_equals(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'equals', value, partition)

    def rule_has_host_name(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'httpHost', value, partition)

    def rule_has_path(self, policy_name, rule_name, value, partition):
        has_httpUri = self.rule_has_condition(
            policy_name, rule_name, 'httpUri', value, partition)
        has_path = self.rule_has_condition(
            policy_name, rule_name, 'path', value, partition)
        return has_httpUri and has_path

    def rule_has_file_type(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'httpUri', value, partition)

    def rule_has_header(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'httpHeader', value, partition)

    def rule_has_cookie(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'httpCookie', value, partition)

    def virtual_server_exists(self, name, partition):
        return self.bigip.tm.ltm.virtuals.virtual.exists(
            name=name, partition=partition)

    def virtual_server_has_policy(self, vs_name, policy_name, partition):
        if self.virtual_server_exists(name=vs_name, partition=partition):
            vs = self.bigip.tm.ltm.virtuals.virtual.load(
                name=vs_name, partition=partition)

            policies = vs.policies_s.get_collection()
            for policy in policies:
                if policy.name == policy_name:
                    return True

        return False
