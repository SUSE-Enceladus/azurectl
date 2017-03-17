# NAME

azurectl - Command Line Interface to manage Microsoft Azure

Azure blobs describe data files living inside of a container managed by an Azure storage account. Several operations in Azure requires those data files to be accessaible from the same region and storage account compared to the origin of the request. Thus blob operations to e.g copy data files between regions and/or accounts are needed and handled in this command.

# SYNOPSIS

__azurectl__ storage blob copy --source-blob=*blob-name*

    [--destination-region=*region*]
    [--destination-storage-account=*storage-account-name*]
    [--destination-container=*storage-container-name*]
    [--destination-blob=*blob-name*]


# DESCRIPTION

## __copy__

Copy data files between regions and storage accounts/containers.

# OPTIONS

# __--source-blob=blob-name__

Name of the blob to copy from

# __--destination-region=region__

Azure region name where the copy will be created. If omitted, the source region will be used as the destination.

# __--destination-storage-account=storage-account-name__

Azure storage account name where the copy will be created. If omitted, the source account will be used as the destination.

NOTE: the supplied storage-account must exist in the destination region.

# __--destination-container=storage-container-name__

Azure storage container name, in the destination storage account, where the copy will be contained. If omitted, the source container will be used as the destination.

NOTE: the supplied storage-container must exist in the destination region and storage account

# __--destination-blob=blob-name__

Name of the copied blob. If ommitted, the source name will be used for the copy.

NOTE: if the source is copied inside of the same region, storage account and container, the destination blob name must be different from the source blob name
