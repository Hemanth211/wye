from datetime import datetime, timedelta

import re
from wye.base.constants import WorkshopStatus
from tests import factories as f


def test_workshop_wrong_action(base_url, browser, outbox):
    tutor_type = f.create_usertype(slug='tutor', display_name='tutor')
    poc_type = f.create_usertype(slug='poc', display_name='poc')

    user = f.create_user()
    user.set_password('123123')
    user.save()
    url = base_url + '/workshop/'
    browser.visit(url)
    browser.fill('login', user.email)
    browser.fill('password', '123123')
    browser.find_by_css('[type=submit]')[0].click()
    assert len(outbox) == 1
    mail = outbox[0]
    confirm_link = re.findall(r'http.*/accounts/.*/', mail.body)
    assert confirm_link
    browser.visit(confirm_link[0])
    assert browser.title, "Confirm E-mail Address"
    browser.find_by_css('[type=submit]')[0].click()

    user.profile.usertype.clear()
    user.profile.usertype.add(poc_type)
    user.save()
    org = f.create_organisation()
    org.user.add(user)
    user.profile.interested_locations.add(org.location)
    user.profile.location = org.location
    user.profile.save()
    org.save()

    workshop = f.create_workshop(requester=org)

    workshop.expected_date = datetime.now() + timedelta(days=20)
    workshop.status = WorkshopStatus.REQUESTED
    workshop.location = org.location
    workshop.save()
    url = base_url + '/workshop/update/{}/'.format(workshop.id)
    browser.visit(url)
    browser.fill('login', user.email)
    browser.fill('password', '123123')
    browser.find_by_css('[type=submit]')[0].click()

    section1 = f.create_workshop_section(name='section1')
    location = org.location
    state = f.create_state(name='state2')

    user.profile.usertype.clear()
    user.profile.usertype.add(tutor_type)

    user.profile.location = location
    user.profile.interested_states.add(state)
    user.profile.mobile = '1234567890'
    user.profile.interested_sections.add(section1)
    user.profile.interested_level = 1
    user.profile.github = 'https://github.com'
    user.profile.occupation = 'occupation'
    user.profile.work_location = 'work_location'
    user.profile.work_experience = 1
    user.profile.save()
    user.save()

    url = base_url + '/workshop/' + 'feedback/000/'
    browser.visit(url)

    url = base_url + '/workshop/feedback/{}/'.format(workshop.id)
    browser.visit(url)


def test_workshop_flow(base_url, browser, outbox):
    tutor_type = f.create_usertype(slug='tutor', display_name='tutor')
    poc_type = f.create_usertype(slug='poc', display_name='poc')
    wr1 = f.create_workshop_rating()
    wr2 = f.create_workshop_rating()
    wr3 = f.create_workshop_rating()
    wr4 = f.create_workshop_rating()
    state1 = f.create_state(name='state1')
    state2 = f.create_state(name='state2')

    user = f.create_user()
    user.set_password('123123')
    user.save()
    url = base_url + '/workshop/'
    browser.visit(url)
    browser.fill('login', user.email)
    browser.fill('password', '123123')
    browser.find_by_css('[type=submit]')[0].click()
    assert len(outbox) == 1
    mail = outbox[0]
    confirm_link = re.findall(r'http.*/accounts/.*/', mail.body)
    assert confirm_link
    browser.visit(confirm_link[0])
    assert browser.title, "Confirm E-mail Address"
    browser.find_by_css('[type=submit]')[0].click()

    user.profile.usertype.clear()
    user.profile.usertype.add(poc_type)
    user.save()
    location = f.create_locaiton(state=state1)
    org = f.create_organisation(location=location)
    org.user.add(user)
    user.profile.interested_locations.add(org.location)
    user.profile.location = org.location
    user.profile.occupation = 'occupation'
    user.profile.work_location = 'work_location'
    user.profile.work_experience = 1
    user.profile.save()
    org.save()

    workshop = f.create_workshop(
        requester=org,
        status=WorkshopStatus.REQUESTED)

    workshop.expected_date = datetime.now() + timedelta(days=20)
    workshop.presenter.add(user)
    workshop.save()
    url = base_url + '/workshop/update/{}/'.format(workshop.id)
    browser.visit(url)
    browser.fill('login', user.email)
    browser.fill('password', '123123')
    browser.find_by_css('[type=submit]')[0].click()

    section1 = f.create_workshop_section(name='section1')
    location = org.location

    user.profile.usertype.clear()
    user.profile.usertype.add(tutor_type)

    user.profile.location = location
    user.profile.interested_states.add(state2)
    user.profile.interested_states.add(state1)
    user.profile.mobile = '1234567890'
    user.profile.interested_sections.add(section1)
    user.profile.interested_level = 1
    user.profile.github = 'https://github.com'
    user.profile.occupation = 'occupation'
    user.profile.work_location = 'work_location'
    user.profile.work_experience = 1
    user.profile.save()
    user.save()

    url = base_url + '/workshop/{}/'.format(workshop.id)
    browser.visit(url)

    accept_workshop_link = browser.find_by_text('Accept')[0]
    assert accept_workshop_link
    accept_workshop_link.click()

    user.profile.usertype.clear()
    user.profile.usertype.add(poc_type)
    user.profile.save()
    user.save()

#   checking to move requested workshop in hold state
    url = base_url + '/workshop/{}/'.format(workshop.id)
    browser.visit(url)
    hold_workshop_link = browser.find_by_text('Hold')[0]
    assert hold_workshop_link
    hold_workshop_link.click()

#   checking to move on hold workshop into requested state
    browser.visit(url)
    publish_workshop_link = browser.find_by_text('Publish/Request')[0]
    assert publish_workshop_link
    publish_workshop_link.click()

    browser.visit(url)
    # browser.screenshot()
    hold_workshop_link = browser.find_by_text('Hold')[0]
    assert hold_workshop_link
    hold_workshop_link.click()

    browser.visit(url)
    publish_workshop_link = browser.find_by_text('Publish/Request')[0]
    assert publish_workshop_link
    publish_workshop_link.click()

    browser.visit(url)
    accept_workshop_link = browser.find_by_text('Accept')[0]
    assert accept_workshop_link
    accept_workshop_link.click()

    workshop.expected_date = datetime.now() + timedelta(days=-60)
    # workshop.status = WorkshopStatus.FEEDBACK_PENDING
    workshop.save()

    browser.visit(url)
    url = base_url + '/workshop/feedback/{}'.format(workshop.id)
    browser.visit(url)
    for wr in [wr1, wr2, wr3, wr4]:
        id = '{}-{}'.format(wr1.feedback_type, wr1.id)
        browser.check(id)
        # browser.check('3-1')
    browser.fill('comment', "Testing comments")

    browser.find_by_css('[type=submit]')[0].click()
