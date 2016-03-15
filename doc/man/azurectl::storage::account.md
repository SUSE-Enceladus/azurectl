# NAME

azurectl - Command Line Interface to manage Microsoft Azure

# SYNOPSIS

__azurectl__ storage account list

__azurectl__ storage account show --name=*storage_account_name*

__azurectl__ storage account create --name=*storage_account_name*

    [--description=<description>]
    [--label=<label>]
    [--locally-redundant|--zone-redundant|--geo-redundant|--read-access-geo-redundant]

__azurectl__ storage account update --name=*storage_account_name*

    [--description=<description>]
    [--label=<label>]
    [--locally-redundant|--zone-redundant|--geo-redundant|--read-access-geo-redundant]
    [--new-primary-key]
    [--new-secondary-key]

__azurectl__ storage account delete --name=*storage_account_name*

# DESCRIPTION

## __list__

List basic attributes of all storage accounts within the selected Azure
subscription.

## __show__

List more detailed attributes of a named storage account, including a list of
containers and storage API keys.

## __create__

Add a new storage account to your Azure subscription. Any additional backup
configuration required for the selected backup strategy, as well as a set of
storage API keys will be generated automatically.

## __update__

Modify a named storage account, updating any combination of attributes as
supplied in the command arguments. Any attribute not explicitly supplied will
be left as-is. Make note of the constraints on some backup strategies, as a
change of strategy may cause data loss. The __update__ command may also be used
to generate new storage API keys, using any combination of the
__--new-primary-key__ and __--new-secondary-key__ arguments.

## __delete__

Destroy a named storage account. All containers, and all storage entries within
those containers, will be destroyed as well. Please not that the operation will
fail if there are leases held on any storage entries within the account.

# TEXT OPTIONS

##__--name=storage_account_name__

The name of the a storage account to access, create, or modify. This is also
the hostname of the storage endpoints within the account; the specific endpoint
URLs are available when __show__ing or __list__ing the account. The name of a
storage account is immutable: it cannot be updated once the account is created.

VALIDATION NOTE: When creating a storage account, the name must be between
three and 24 characters in length, and may only contain numbers and lowercase
letters.

##__--description=description__

A text description of the storage account, up to 1024 characters in length.

##__--label=label__

Because of the limitations on valid storage account names, you may prefer to use
a label to identify a storage account's function. Labels are up to 100
characters in length.

# BACKUP STRATEGY OPTIONS

Each storage account is configured with some backup strategy in order to ensure
data integrity. The following options are avaliable during __create__ and
__update__ actions, to define the backup strategy on a storage account. The
cost of operating a storage account may be affected by the strategy. C

##__--locally-redundant__

Three replicas of all data are stored, but only within the storage account's
primary region. ( 3 total copies )

##__--zone-redundant__

Block blobs are replicated across two or three facilities, in one or two
regions. No other storage types are allowed on a zone-redundant account.
( 6 total copies, only block blobs )

NOTE: you cannot change from zone-redundant to another backup strategy.

##__--geo-redundant__

Data is replicated to a secondary region; first data is replicated like
locally-redundant storage, then replicated again like locally-redunant storage
in an additonal region. In the event of a major outage in the storage account's
primary region, data will be restored from the secondary region.
( 6 total copies )

NOTE: if no backup strategy is selected, this is the default.

##__--read-access-geo-redundant__

Like geo-redundant storage, but in addition a second endpoint is available
with read-only permissions. The read-only backup is available even during an
outage in the primary region. (6 total copies, plus read-only access)

# UPDATING API KEYS

When a storage account is created, a pair of API keys are generated
automatically. In the event new keys are required, the following options may
be passed to the __update__ command, in order to trigger regeneration.

Any new keys will be displayed after the update is complete, and the old keys
they replaced will no longer be valid.

##__--new-primary-key__

Replaces only the primary key.

##__--new-secondary-key__

Replaces only the secondary key.