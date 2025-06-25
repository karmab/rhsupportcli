from ast import literal_eval
import argparse
from argparse import RawDescriptionHelpFormatter as rawhelp
import json
from prettytable import PrettyTable
import os
from rhsupportlib import RHsupportClient
import sys

PARAMHELP = "specify parameter or keyword for rendering (multiple can be specified)"


def parse_parameters(param=[]):
    overrides = {}
    for x in param or []:
        if len(x.split('=')) < 2:
            continue
        else:
            if len(x.split('=')) == 2:
                key, value = x.split('=')
            else:
                split = x.split('=')
                key = split[0]
                value = x.replace(f"{key}=", '')
            if value.isdigit():
                value = int(value)
            elif value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value == '[]':
                value = []
            elif value.startswith('{') and value.endswith('}') and not value.startswith('{\"ignition'):
                value = literal_eval(value)
            elif value.startswith('[') and value.endswith(']'):
                if '{' in value:
                    value = literal_eval(value)
                else:
                    value = value[1:-1].split(',')
                    for index, v in enumerate(value):
                        v = v.strip()
                        value[index] = v
            overrides[key] = value
    return overrides


def get_subparser_print_help(parser, subcommand):
    subparsers_actions = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)]
    for subparsers_action in subparsers_actions:
        for choice, subparser in subparsers_action.choices.items():
            if choice == subcommand:
                subparser.print_help()
                return


def get_subparser(parser, subcommand):
    subparsers_actions = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)]
    for subparsers_action in subparsers_actions:
        for choice, subparser in subparsers_action.choices.items():
            if choice == subcommand:
                return subparser


def create_case(args):
    parameters = parse_parameters(args.param)
    rhc = RHsupportClient()
    print(rhc.create_case(parameters))


def create_attachment(args):
    rhc = RHsupportClient()
    print(rhc.create_attachment(args.case, args.path))


def create_comment(args):
    rhc = RHsupportClient()
    print(rhc.create_comment(args.case, args.comment))


def get_account(args):
    rhc = RHsupportClient()
    print(rhc.get_account())


def list_customers(args):
    rhc = RHsupportClient()
    customerstable = PrettyTable(["Mail"])
    for customer in sorted(rhc.list_customers(args.account), key=lambda x: x['email']):
        customerstable.add_row([customer['email']])
    print(customerstable)


def list_partners(args):
    rhc = RHsupportClient()
    partnerstable = PrettyTable(["Mail"])
    for partner in rhc.list_partners(args.account):
        partnerstable.add_row([partner['email']])
    print(partnerstable)


def list_contacts(args):
    rhc = RHsupportClient()
    contactstable = PrettyTable(["Mail"])
    for contact in sorted(rhc.list_contacts(args.account), key=lambda x: x['email']):
        contactstable.add_row([contact['email']])
    print(contactstable)


def get_attachments(args):
    rhc = RHsupportClient()
    print(rhc.get_attachments(args.case, args.path))


def get_case(args):
    rhc = RHsupportClient()
    case = rhc.get_case(args.case)
    print(f"id: {case['caseNumber']}")
    print(f"status: {case['status']}")
    print(f"summary: {case['summary']}")
    print(f"description: {case['description']}")
    comments = rhc.get_comments(args.case)
    print("------------")
    for index, comment in enumerate(reversed(sorted(comments, key=lambda x: x['lastModifiedDate']))):
        print(f"Comment {len(comments) - index}:")
        print(comment['commentBody'])
        print("------------")


def list_cases(args):
    parameters = parse_parameters(args.param)
    rhc = RHsupportClient()
    casestable = PrettyTable(["Id", "Status", "Summary"])
    for case in rhc.list_cases(parameters):
        entry = case['caseNumber'], case['status'], case['summary']
        casestable.add_row(entry)
    print(casestable)


def list_case_keywords(args):
    obj = 'UpdateCaseRequest' if args.update else 'Case'
    codedir = os.path.dirname(list_cases.__code__.co_filename)
    with open(f'{codedir}/CaseManagement-API_v1.json') as f:
        data = json.load(f)
        for key in sorted(data['definitions'][obj]['properties'].keys()):
            print(key)


def update_case(args):
    parameters = parse_parameters(args.param)
    rhc = RHsupportClient()
    update = rhc.update_case(args.case, parameters)
    sys.exit(1 if update is not None else 0)


def get_business_hours(args):
    rhc = RHsupportClient()
    data = rhc.get_business_hours(args.timezone)
    businesshourstable = PrettyTable(["Day", "Start", "End"])
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
        entry = [day, data[f'{day}StartTime'], data[f'{day}EndTime']]
        businesshourstable.add_row(entry)
    print(businesshourstable)


def search_cases(args):
    parameters = parse_parameters(args.param)
    rhc = RHsupportClient()
    data = rhc.search_cases(parameters)
    print(data)


def search_kcs(args):
    parameters = parse_parameters(args.param)
    rhc = RHsupportClient()
    data = rhc.search_kcs(parameters)
    print(data)


def cli():
    parser = argparse.ArgumentParser(description='RH Support client')
    parser.add_argument('--offlinetoken', default=os.environ.get('OFFLINETOKEN'))
    parser.add_argument('-t', '--token', default=os.environ.get('TOKEN'))
    subparsers = parser.add_subparsers(metavar='', title='Available Commands')

    create_desc = 'Create object'
    create_parser = subparsers.add_parser('create', description=create_desc, help=create_desc, aliases=['add'])
    create_subparsers = create_parser.add_subparsers(metavar='', dest='subcommand_create')

    casecreate_desc = 'Create case'
    casecreate_parser = create_subparsers.add_parser('case', description=casecreate_desc,
                                                     help=casecreate_desc, formatter_class=rawhelp)
    casecreate_parser.add_argument('-P', '--param', action='append', help=PARAMHELP, metavar='PARAM')
    casecreate_parser.set_defaults(func=create_case)

    attachmentcreate_desc = 'Create case comment'
    attachmentcreate_parser = create_subparsers.add_parser('attachment', description=attachmentcreate_desc,
                                                           help=attachmentcreate_desc, formatter_class=rawhelp,
                                                           aliases=['attachments'])
    attachmentcreate_parser.add_argument('case', metavar='CASE')
    attachmentcreate_parser.add_argument('path', metavar='PATH')
    attachmentcreate_parser.set_defaults(func=create_attachment)

    commentcreate_desc = 'Create case comment'
    commentcreate_parser = create_subparsers.add_parser('comment', description=commentcreate_desc,
                                                        help=commentcreate_desc, formatter_class=rawhelp)
    commentcreate_parser.add_argument('case', metavar='CASE')
    commentcreate_parser.add_argument('comment', metavar='COMMENT')
    commentcreate_parser.set_defaults(func=create_comment)

    # delete_desc = 'Delete Object'
    # delete_parser = subparsers.add_parser('delete', description=delete_desc, help=delete_desc, aliases=['remove'])
    # delete_parser.add_argument('-y', '--yes', action='store_true', help='Dont ask for confirmation', dest="yes_top")
    # delete_subparsers = delete_parser.add_subparsers(metavar='', dest='subcommand_delete')

    download_desc = 'Download assets'
    download_parser = subparsers.add_parser('download', description=download_desc, help=download_desc)
    download_subparsers = download_parser.add_subparsers(metavar='', dest='subcommand_download')

    attachmentsdownload_desc = 'Download attachments'
    attachmentsdownload_parser = argparse.ArgumentParser(add_help=False)
    attachmentsdownload_parser.add_argument('-p', '--path', metavar='PATH', default='.', help='Where to download')
    attachmentsdownload_parser.add_argument('case', metavar='CASE')
    attachmentsdownload_parser.set_defaults(func=get_attachments)
    download_subparsers.add_parser('attachments', parents=[attachmentsdownload_parser],
                                   description=attachmentsdownload_desc,
                                   help=attachmentsdownload_desc)

    get_desc = 'Get object'
    get_parser = subparsers.add_parser('get', description=get_desc, help=get_desc, aliases=['info'])
    get_subparsers = get_parser.add_subparsers(metavar='', dest='subcommand_get')

    accountget_desc = 'Get account'
    accountget_parser = get_subparsers.add_parser('account', description=accountget_desc,
                                                  help=accountget_desc, formatter_class=rawhelp)
    accountget_parser.set_defaults(func=get_account)

    businesshoursget_desc = 'Get business hours'
    businesshoursget_parser = get_subparsers.add_parser('businesshours', description=businesshoursget_desc,
                                                        help=businesshoursget_desc, formatter_class=rawhelp)
    businesshoursget_parser.add_argument('timezone', metavar='TIMEZONE')
    businesshoursget_parser.set_defaults(func=get_business_hours)

    caseget_desc = 'Get case'
    caseget_parser = get_subparsers.add_parser('case', description=caseget_desc,
                                               help=caseget_desc, formatter_class=rawhelp)
    caseget_parser.add_argument('-c', '--comments', action='store_true', help='Display comments')
    caseget_parser.add_argument('case', metavar='CASE')
    caseget_parser.set_defaults(func=get_case)

    list_desc = 'List object'
    list_parser = subparsers.add_parser('list', description=list_desc, help=list_desc)
    list_subparsers = list_parser.add_subparsers(metavar='', dest='subcommand_list')

    case_list_desc = 'List cases'
    case_list_parser = argparse.ArgumentParser(add_help=False)
    case_list_parser.add_argument('-P', '--param', action='append', help=PARAMHELP, metavar='PARAM')
    case_list_parser.set_defaults(func=list_cases)
    list_subparsers.add_parser('case', parents=[case_list_parser], description=case_list_desc,
                               help=case_list_desc, aliases=['cases'])

    casekeyword_list_desc = 'List case keywords'
    casekeyword_list_parser = argparse.ArgumentParser(add_help=False)
    casekeyword_list_parser.add_argument('-u', '--update', action='store_true', help='Report update values')
    casekeyword_list_parser.set_defaults(func=list_case_keywords)
    list_subparsers.add_parser('case-keyword', parents=[casekeyword_list_parser], description=casekeyword_list_desc,
                               help=casekeyword_list_desc, aliases=['case-keywords'])

    contacts_list_desc = 'List contacts'
    contacts_list_parser = list_subparsers.add_parser('contact', description=contacts_list_desc,
                                                      help=contacts_list_desc, formatter_class=rawhelp,
                                                      aliases=['contacts'])
    contacts_list_parser.add_argument('account', metavar='ACCOUNT', nargs='?')
    contacts_list_parser.set_defaults(func=list_contacts)

    customers_list_desc = 'List customers'
    customers_list_parser = list_subparsers.add_parser('customer', description=customers_list_desc,
                                                       help=customers_list_desc, formatter_class=rawhelp,
                                                       aliases=['customers'])
    customers_list_parser.add_argument('account', metavar='ACCOUNT', nargs='?')
    customers_list_parser.set_defaults(func=list_customers)

    partners_list_desc = 'List partners'
    partners_list_parser = list_subparsers.add_parser('partner', description=partners_list_desc,
                                                      help=partners_list_desc, formatter_class=rawhelp,
                                                      aliases=['partners'])
    partners_list_parser.add_argument('account', metavar='ACCOUNT', nargs='?')
    partners_list_parser.set_defaults(func=list_partners)

    search_desc = 'Search object'
    search_parser = subparsers.add_parser('search', description=search_desc, help=search_desc)
    search_subparsers = search_parser.add_subparsers(metavar='', dest='subcommand_search')

    cases_search_desc = 'Search cases'
    cases_search_parser = search_subparsers.add_parser('case', description=cases_search_desc,
                                                       help=cases_search_desc, formatter_class=rawhelp,
                                                       aliases=['cases'])
    cases_search_parser.add_argument('-P', '--param', action='append', help=PARAMHELP, metavar='PARAM')
    cases_search_parser.set_defaults(func=search_cases)

    kcs_search_desc = 'Search kcs'
    kcs_search_parser = search_subparsers.add_parser('kcs', description=kcs_search_desc,
                                                     help=kcs_search_desc, formatter_class=rawhelp)
    kcs_search_parser.add_argument('-P', '--param', action='append', help=PARAMHELP, metavar='PARAM')
    kcs_search_parser.set_defaults(func=search_kcs)

    update_desc = 'Update object'
    update_parser = subparsers.add_parser('update', description=update_desc, help=update_desc, aliases=['patch'])
    update_subparsers = update_parser.add_subparsers(metavar='', dest='subcommand_update')

    caseupdate_desc = 'Update case'
    caseupdate_parser = argparse.ArgumentParser(add_help=False)
    caseupdate_parser.add_argument('-P', '--param', action='append', help=PARAMHELP, metavar='PARAM')
    caseupdate_parser.add_argument('case', metavar='CASE')
    caseupdate_parser.set_defaults(func=update_case)
    update_subparsers.add_parser('case', parents=[caseupdate_parser], description=caseupdate_desc, help=caseupdate_desc)

    if len(sys.argv) == 1:
        parser.print_help()
        os._exit(0)
    args = parser.parse_args()
    if not hasattr(args, 'func'):
        for attr in dir(args):
            if attr.startswith('subcommand_') and getattr(args, attr) is None:
                split = attr.split('_')
                if len(split) == 2:
                    subcommand = split[1]
                    get_subparser_print_help(parser, subcommand)
                elif len(split) == 3:
                    subcommand = split[1]
                    subsubcommand = split[2]
                    subparser = get_subparser(parser, subcommand)
                    get_subparser_print_help(subparser, subsubcommand)
                os._exit(0)
        os._exit(0)
    args.func(args)


if __name__ == '__main__':
    cli()
