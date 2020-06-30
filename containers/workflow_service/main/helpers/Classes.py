class StateObject:
    def __init__(self, delta_state, description, feature, post_state, pre_state, state_units):
        self.delta_state = delta_state
        self.description = description
        self.feature = feature
        self.post_state = post_state
        self.pre_state = pre_state
        self.state_units = state_units

class NodeRouteObject:
    def __init__(self, route_string, route_id, contact_list_id):
        self.route_string = route_string
        self.route_id = route_id
        self.contact_list_id = contact_list_id

class LastStateChangeObject:
    def __init__(self, state_change_date, states):
        self.state_change_date = state_change_date
        self.states = states

class WellObject:
    def __init__(self, default_assignee, default_assignee_user_id, no_comms, last_state_change_object, route_object, production_average, team):
        self.default_assignee = default_assignee
        self.default_assignee_user_id = default_assignee_user_id
        self.no_comms = no_comms
        self.last_state_change_object = last_state_change_object
        self.route_object = route_object
        self.production_average = production_average
        self.team = team
