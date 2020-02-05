import json
import unittest

class DtkModuleTest(unittest.TestCase):
    def setUp(self, *args, **kwargs):
        self.root_methods = [
            'create', 'get_age','get_immunity', 'get_infection_age',
            'get_infectiousness', 'get_schema', 'give_intervention', 'is_infected',
            'is_possible_mother', 'is_pregnant', 'my_set_callback', 'reset','serialize',
            'set_deposit_callback', 'set_enum_param', 'set_mortality_callback', 'set_param',
            'should_infect', 'update', 'update1', 'update2', 'update_pregnancy'
        ]
        self.missing_methods = [ 'get_individual']
        self.debug = False
        self.namespace_under_test = None


    def create_generic_male_female(self, male, female):
        expected_toby = {}
        expected_toby['age'] = 7300.0
        expected_toby['sex'] = 0
        expected_toby['mcw'] = 1.1
        male['expected'] = expected_toby  # Male, 23 years, monte carlo weight 1.0

        expected_tina = {}
        expected_tina['age'] = 3650.0
        expected_tina['sex'] = 1
        expected_tina['mcw'] = 0.9
        female['expected'] = expected_tina  # Female, 10 years, monte carlo weight 1.0

        male_human = self.create_individual_hook(expected_toby['sex'],
                                                 expected_toby['age'],
                                                 expected_toby['mcw'])
        female_human = self.create_individual_hook(expected_tina['sex'],
                                                   expected_tina['age'],
                                                   expected_tina['mcw'])
        male['observed'] = male_human
        female['observed'] = female_human

    def serialize_male_female(self, male, female):
        self.assertTrue(male, "Male should be populated before serializing.")
        self.assertTrue(female, "Female should be populated before serializing.")
        male['serialized'] = self.serialize_individual_hook(male['observed'], male['label'])
        female['serialized'] = self.serialize_individual_hook(female['observed'], female['label'])

    def create_individual_hook(self, sex_int, age_float, mcw_float):
        return self.namespace_under_test.create((sex_int, age_float, mcw_float))

    def serialize_individual_hook(self, individual, individual_label=None):
        individual_text = self.namespace_under_test.serialize(individual)
        individual_json = json.loads(individual_text)
        if self.debug:
            if not individual_label:
                individual_label = f"Individual with id {individual_json['individual']['suid']['id']}"
            with open(f'{individual_label}.json', 'w') as outfile:
                json.dump(individual_json, outfile, indent=4, sort_keys=True)
        return individual_json

    def check_property_of_individual(self, property_under_test, expected_value,
                                     observed_value, individual_label=None):
        self.assertEqual(expected_value, observed_value, msg=f'{individual_label} should have {property_under_test} '\
                                                             f'of {expected_value}, observed: {observed_value}.\n')

    def compare_generic_individual_with_expectations(self, expected_individual,
                                                     observed_serialized_individual,
                                                     individual_label=None):
        if not individual_label:
            individual_label = f"Individual with id {observed_serialized_individual['suid']['id']}"
        self.check_property_of_individual('age', expected_individual['age'],
                                          observed_serialized_individual['m_age'],
                                          individual_label=individual_label)
        self.check_property_of_individual("sex", expected_individual['sex'],
                                          observed_serialized_individual['m_gender'],
                                          individual_label=individual_label)
        self.check_property_of_individual("monte carlo weight", expected_individual['mcw'],
                                          observed_serialized_individual['m_mc_weight'],
                                          individual_label=individual_label)

    def report_missing_methods(self, namespace_name, methodlist, namespace, package_name=None):
        '''

        :param namespace_name: label for logging messages
        :param methodlist: array of properties to check for
        :param namespace: the actual thing that you imported, we'll call dir() on this
        :param package_name: defaults to None, doesn't seem to do anything yet
        :return:
        '''
        self.assertIsNotNone(namespace)
        listing = dir(namespace)
        missing_properties = []
        for em in methodlist:
            if em not in listing:
                missing_properties.append(em)
        self.assertEqual(0, len(missing_properties), msg=f"Expected no missing properties in {namespace_name},"
                                                         f" missing: {str(missing_properties)}")
        pass
    pass
