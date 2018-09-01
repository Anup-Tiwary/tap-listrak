import singer
from singer import metrics, metadata, Transformer

from tap_listrak.schema import PKS

def write_schema(catalog, stream_id):
    stream = catalog.get_stream(stream_id)
    schema = stream.schema.to_dict()
    key_properties = PKS[stream_id]
    singer.write_schema(stream_id, schema, key_properties)

def persist_records(catalog, stream_id, records):
    stream = catalog.get_stream(stream_id)
    schema = stream.schema.to_dict()
    stream_metadata = metadata.to_map(stream.metadata)
    with metrics.record_counter(stream_id) as counter:
        for record in records:
            with Transformer() as transformer:
                record = transformer.transform(record,
                                               schema,
                                               stream_metadata)
            singer.write_record(stream_id, record)
            counter.increment()

def nested_get(dic, keys, default_value):
    cur_dic = dic
    for key in keys[:-1]:
        if key in cur_dic:
            cur_dic = cur_dic[key]
        else:
            return default_value

    if keys[-1] in cur_dic:
        return cur_dic[keys[-1]]

    return default_value

def nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value

def get_selected_streams(catalog):
    selected_streams = set()
    for stream in catalog.streams:
        mdata = metadata.to_map(stream.metadata)
        root_metadata = mdata.get(())
        if root_metadata and root_metadata.get('selected') is True:
            selected_streams.add(stream.tap_stream_id)
    return list(selected_streams)

def sync_lists(client, catalog, persist):
    lists, _ = client.get('/List')
    if persist:
        write_schema(catalog, 'lists')
        persist_records(catalog, 'lists', lists)
    return lists

def sync_campaigns(client, catalog, list_id):
    campaigns, _ = client.get('/List/{}/Campaign'.format(list_id))
    def transform_campaign(row):
        row['listId'] = list_id
        return row
    campaigns = map(transform_campaign, campaigns)
    write_schema(catalog, 'campaigns')
    persist_records(catalog, 'campaigns', campaigns)

def sync_contact_page(client, list_id, subscription_state, start_date, next_token):
    return client.get(
        '/List/{}/Contact'.format(list_id),
        params={
            'cursor': next_token,
            'subscriptionState': subscription_state,
            'startDate': start_date,
            'count': 5000
        })

def get_contacts_bookmark(state, list_id, contact_state, start_date):
    return nested_get(state, ['bookmarks', list_id, 'contacts', contact_state], start_date)

def write_contacts_bookmark(state, list_id, contact_state, max_date):
    nested_set(state, ['bookmarks', list_id, 'contacts', contact_state], max_date)
    singer.write_state(state)

def sync_contacts_subscription_state(state, client, catalog, start_date, list_id, subscription_state):
    if subscription_state == 'Subscribed':
        date_key = 'subscribeDate'
    else:
        date_key = 'unsubscribeDate'

    max_date = start_date
    next_token = 'Start'
    while next_token is not None:
        contacts, next_token = sync_contact_page(client,
                                                 list_id,
                                                 subscription_state,
                                                 start_date,
                                                 next_token)
        persist_records(catalog, 'contacts', contacts)

        if contacts:
            max_data_date = max(contacts, key=lambda x: x[date_key])[date_key]
            if max_data_date > max_date:
                max_date = max_data_date

    # stream is not ordered, so we have to persist state at the end
    write_contacts_bookmark(state, list_id, subscription_state, max_date)

def sync_contacts(client, catalog, state, start_date, list_id):
    write_schema(catalog, 'contacts')

    subscribed_last_date = get_contacts_bookmark(state, list_id, 'Subscribed', start_date)
    sync_contacts_subscription_state(state,
                                     client,
                                     catalog,
                                     subscribed_last_date,
                                     list_id,
                                     'Subscribed')

    unsubscribed_last_date = get_contacts_bookmark(state, list_id, 'Unsubscribed', start_date)
    sync_contacts_subscription_state(state,
                                     client,
                                     catalog,
                                     unsubscribed_last_date,
                                     list_id,
                                     'Unsubscribed')

def sync(client, catalog, state, start_date):
    selected_streams = get_selected_streams(catalog)

    if not selected_streams:
        return

    lists = sync_lists(client, catalog, 'lists' in selected_streams)
 
    list_ids = map(lambda x: x['listId'], lists)

    for list_id in list_ids:
        if 'campaigns' in selected_streams:
            sync_campaigns(client, catalog, list_id)

        if 'contacts' in selected_streams:
            sync_contacts(client, catalog, state, start_date, list_id)
        break
