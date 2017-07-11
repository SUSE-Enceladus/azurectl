# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


class AzureError(Exception):
    """
        Base class to handle all known exceptions. Specific exceptions
        are sub classes of this base class
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class AzureAccountConfigurationError(AzureError):
    pass


class AzureAccountDefaultSectionNotFound(AzureError):
    pass


class AzureAccountLoadFailed(AzureError):
    pass


class AzureBlobServicePropertyError(AzureError):
    pass


class AzureCannotInit(AzureError):
    pass


class AzureCloudServiceAddCertificateError(AzureError):
    pass


class AzureCloudServiceAddressError(AzureError):
    pass


class AzureCloudServiceCreateError(AzureError):
    pass


class AzureCloudServiceDeleteError(AzureError):
    pass


class AzureCloudServicePropertiesError(AzureError):
    pass


class AzureCloudServiceOpenSSLError(AzureError):
    pass


class AzureCommandNotLoaded(AzureError):
    pass


class AzureConfigDefaultLinkError(AzureError):
    pass


class AzureConfigAccountFileNotFound(AzureError):
    pass


class AzureConfigAccountNotFound(AzureError):
    pass


class AzureConfigAddAccountSectionError(AzureError):
    pass


class AzureConfigAddRegionSectionError(AzureError):
    pass


class AzureConfigParseError(AzureError):
    pass


class AzureConfigPublishSettingsError(AzureError):
    pass


class AzureConfigRegionNotFound(AzureError):
    pass


class AzureConfigSectionNotFound(AzureError):
    pass


class AzureConfigVariableNotFound(AzureError):
    pass


class AzureConfigWriteError(AzureError):
    pass


class AzureContainerCreateError(AzureError):
    pass


class AzureContainerDeleteError(AzureError):
    pass


class AzureContainerListContentError(AzureError):
    pass


class AzureContainerListError(AzureError):
    pass


class AzureCustomDataTooLargeError(AzureError):
    pass


class AzureDataDiskAttachError(AzureError):
    pass


class AzureDataDiskCreateError(AzureError):
    pass


class AzureDataDiskDeleteError(AzureError):
    pass


class AzureDataDiskNoAvailableLun(AzureError):
    pass


class AzureDataDiskShowError(AzureError):
    pass


class AzureDomainLookupError(AzureError):
    pass


class AzureEndpointCreateError(AzureError):
    pass


class AzureEndpointDeleteError(AzureError):
    pass


class AzureEndpointListError(AzureError):
    pass


class AzureEndpointShowError(AzureError):
    pass


class AzureEndpointUpdateError(AzureError):
    pass


class AzureFileShareCreateError(AzureError):
    pass


class AzureFileShareDeleteError(AzureError):
    pass


class AzureFileShareListError(AzureError):
    pass


class AzureHelpNoCommandGiven(AzureError):
    pass


class AzureImageNotReachableByCloudServiceError(AzureError):
    pass


class AzureInvalidCommand(AzureError):
    pass


class AzureLoadCommandUndefined(AzureError):
    pass


class AzureManagementCertificateNotFound(AzureError):
    pass


class AzureOsImageCreateError(AzureError):
    pass


class AzureOsImageDeleteError(AzureError):
    pass


class AzureOsImageDetailsShowError(AzureError):
    pass


class AzureOsImageListError(AzureError):
    pass


class AzureOsImagePublishError(AzureError):
    pass


class AzureOsImageReplicateError(AzureError):
    pass


class AzureOsImageShowError(AzureError):
    pass


class AzureOsImageUnReplicateError(AzureError):
    pass


class AzureOsImageUpdateError(AzureError):
    pass


class AzurePageBlobAlignmentViolation(AzureError):
    pass


class AzurePageBlobSetupError(AzureError):
    pass


class AzurePageBlobUpdateError(AzureError):
    pass


class AzurePageBlobZeroPageError(AzureError):
    pass


class AzureRequestError(AzureError):
    pass


class AzureRequestStatusError(AzureError):
    pass


class AzureRequestTimeout(AzureError):
    pass


class AzureReservedIpAssociateError(AzureError):
    pass


class AzureReservedIpDisAssociateError(AzureError):
    pass


class AzureReservedIpCreateError(AzureError):
    pass


class AzureReservedIpDeleteError(AzureError):
    pass


class AzureReservedIpListError(AzureError):
    pass


class AzureReservedIpShowError(AzureError):
    pass


class AzureSSHKeyFileNotFound(AzureError):
    pass


class AzureServiceManagementError(AzureError):
    pass


class AzureServiceManagementUrlNotFound(AzureError):
    pass


class AzureStorageAccountCreateError(AzureError):
    pass


class AzureStorageAccountDeleteError(AzureError):
    pass


class AzureStorageAccountListError(AzureError):
    pass


class AzureStorageAccountShowError(AzureError):
    pass


class AzureStorageAccountUpdateError(AzureError):
    pass


class AzureStorageDeleteError(AzureError):
    pass


class AzureStorageFileNotFound(AzureError):
    pass


class AzureStorageListError(AzureError):
    pass


class AzureStorageNotReachableByCloudServiceError(AzureError):
    pass


class AzureStorageStreamError(AzureError):
    pass


class AzureStorageUploadError(AzureError):
    pass


class AzureSubscriptionCertificateDecodeError(AzureError):
    pass


class AzureSubscriptionIdNotFound(AzureError):
    pass


class AzureSubscriptionPKCS12DecodeError(AzureError):
    pass


class AzureSubscriptionParseError(AzureError):
    pass


class AzureSubscriptionPrivateKeyDecodeError(AzureError):
    pass


class AzureUnknownCommand(AzureError):
    pass


class AzureUnknownServiceName(AzureError):
    pass


class AzureUnrecognizedManagementUrl(AzureError):
    pass


class AzureVmCreateError(AzureError):
    pass


class AzureVmDeleteError(AzureError):
    pass


class AzureVmRebootError(AzureError):
    pass


class AzureVmShutdownError(AzureError):
    pass


class AzureVmStartError(AzureError):
    pass
