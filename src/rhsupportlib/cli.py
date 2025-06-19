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


def create_comment(args):
    rhc = RHsupportClient()
    print(rhc.create_comment(args.case, args.comment))


def delete_case(args):
    print("TODO")


def download_attachments(args):
    print("TODO")


def get_case(args):
    rhc = RHsupportClient()
    case = rhc.get_case(args.case)
    print(f"id: {case['caseNumber']}")
    print(f"status: {case['status']}")
    print(f"summary: {case['summary']}")
    print(f"description: {case['description']}")
    comments = rhc.get_case_comments(args.case)
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


def cli():
    parser = argparse.ArgumentParser(description='RH Support client')
    parser.add_argument('--offlinetoken', default=os.environ.get('OFFLINETOKEN'))
    parser.add_argument('-t', '--token', default=os.environ.get('TOKEN'))
    subparsers = parser.add_subparsers(metavar='', title='Available Commands')

    create_desc = 'Create Object'
    create_parser = subparsers.add_parser('create', description=create_desc, help=create_desc, aliases=['add'])
    create_subparsers = create_parser.add_subparsers(metavar='', dest='subcommand_create')

    casecreate_desc = 'Create Case'
    casecreate_parser = create_subparsers.add_parser('case', description=casecreate_desc,
                                                     help=casecreate_desc, formatter_class=rawhelp)
    casecreate_parser.add_argument('-P', '--param', action='append', help=PARAMHELP, metavar='PARAM')
    casecreate_parser.set_defaults(func=create_case)

    commentcreate_desc = 'Create Case comment'
    commentcreate_parser = create_subparsers.add_parser('comment', description=commentcreate_desc,
                                                        help=commentcreate_desc, formatter_class=rawhelp)
    commentcreate_parser.add_argument('case', metavar='CASE')
    commentcreate_parser.add_argument('comment', metavar='COMMENT')
    commentcreate_parser.set_defaults(func=create_comment)

    delete_desc = 'Delete Object'
    delete_parser = subparsers.add_parser('delete', description=delete_desc, help=delete_desc, aliases=['remove'])
    delete_parser.add_argument('-y', '--yes', action='store_true', help='Dont ask for confirmation', dest="yes_top")
    delete_subparsers = delete_parser.add_subparsers(metavar='', dest='subcommand_delete')

    casedelete_desc = 'Delete Case'
    casedelete_parser = delete_subparsers.add_parser('case', description=casedelete_desc,
                                                     help=casedelete_desc, formatter_class=rawhelp,
                                                     aliases=['deployment'])
    casedelete_parser.add_argument('-y', '--yes', action='store_true', help='Dont ask for confirmation')
    casedelete_parser.add_argument('cases', metavar='CASES', nargs='*')
    casedelete_parser.set_defaults(func=delete_case)

    download_desc = 'Download Assets'
    download_parser = subparsers.add_parser('download', description=download_desc, help=download_desc)
    download_subparsers = download_parser.add_subparsers(metavar='', dest='subcommand_download')

    attachmentsdownload_desc = 'Download Attachments'
    attachmentsdownload_parser = argparse.ArgumentParser(add_help=False)
    attachmentsdownload_parser.add_argument('-p', '--path', metavar='PATH', default='.', help='Where to download asset')
    attachmentsdownload_parser.add_argument('case', metavar='CASE')
    attachmentsdownload_parser.set_defaults(func=download_attachments)
    download_subparsers.add_parser('attachments', parents=[attachmentsdownload_parser],
                                   description=attachmentsdownload_desc,
                                   help=attachmentsdownload_desc)

    get_desc = 'Get Object'
    get_parser = subparsers.add_parser('get', description=get_desc, help=get_desc, aliases=['info'])
    get_subparsers = get_parser.add_subparsers(metavar='', dest='subcommand_get')

    caseget_desc = 'Get Case'
    caseget_parser = get_subparsers.add_parser('case', description=caseget_desc,
                                               help=caseget_desc, formatter_class=rawhelp)
    caseget_parser.add_argument('-c', '--comments', action='store_true', help='Display comments')
    caseget_parser.add_argument('case', metavar='CASE')
    caseget_parser.set_defaults(func=get_case)

    list_desc = 'List Object'
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

    update_desc = 'Update Object'
    update_parser = subparsers.add_parser('update', description=update_desc, help=update_desc, aliases=['patch'])
    update_subparsers = update_parser.add_subparsers(metavar='', dest='subcommand_update')

    caseupdate_desc = 'Update Case'
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
