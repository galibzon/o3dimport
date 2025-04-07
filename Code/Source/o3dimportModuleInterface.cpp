
#include "o3dimportModuleInterface.h"
#include <AzCore/Memory/Memory.h>

#include <o3dimport/o3dimportTypeIds.h>

namespace o3dimport
{
    AZ_TYPE_INFO_WITH_NAME_IMPL(o3dimportModuleInterface,
        "o3dimportModuleInterface", o3dimportModuleInterfaceTypeId);
    AZ_RTTI_NO_TYPE_INFO_IMPL(o3dimportModuleInterface, AZ::Module);
    AZ_CLASS_ALLOCATOR_IMPL(o3dimportModuleInterface, AZ::SystemAllocator);

    o3dimportModuleInterface::o3dimportModuleInterface()
    {
    }

    AZ::ComponentTypeList o3dimportModuleInterface::GetRequiredSystemComponents() const
    {
        return AZ::ComponentTypeList{
        };
    }
} // namespace o3dimport
