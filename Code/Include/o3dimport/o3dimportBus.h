
#pragma once

#include <o3dimport/o3dimportTypeIds.h>

#include <AzCore/EBus/EBus.h>
#include <AzCore/Interface/Interface.h>

namespace o3dimport
{
    class o3dimportRequests
    {
    public:
        AZ_RTTI(o3dimportRequests, o3dimportRequestsTypeId);
        virtual ~o3dimportRequests() = default;
        // Put your public methods here
    };

    class o3dimportBusTraits
        : public AZ::EBusTraits
    {
    public:
        //////////////////////////////////////////////////////////////////////////
        // EBusTraits overrides
        static constexpr AZ::EBusHandlerPolicy HandlerPolicy = AZ::EBusHandlerPolicy::Single;
        static constexpr AZ::EBusAddressPolicy AddressPolicy = AZ::EBusAddressPolicy::Single;
        //////////////////////////////////////////////////////////////////////////
    };

    using o3dimportRequestBus = AZ::EBus<o3dimportRequests, o3dimportBusTraits>;
    using o3dimportInterface = AZ::Interface<o3dimportRequests>;

} // namespace o3dimport
