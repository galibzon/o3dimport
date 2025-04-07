
#include <AzCore/Serialization/SerializeContext.h>
#include "o3dimportEditorSystemComponent.h"

#include <o3dimport/o3dimportTypeIds.h>

namespace o3dimport
{
    AZ_COMPONENT_IMPL(o3dimportEditorSystemComponent, "o3dimportEditorSystemComponent",
        o3dimportEditorSystemComponentTypeId);

    void o3dimportEditorSystemComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<o3dimportEditorSystemComponent, AZ::Component>();
        }
    }

    o3dimportEditorSystemComponent::o3dimportEditorSystemComponent()
    {
        if (o3dimportInterface::Get() == nullptr)
        {
            o3dimportInterface::Register(this);
        }
    }

    o3dimportEditorSystemComponent::~o3dimportEditorSystemComponent()
    {
        if (o3dimportInterface::Get() == this)
        {
            o3dimportInterface::Unregister(this);
        }
    }

    void o3dimportEditorSystemComponent::GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided)
    {
        provided.push_back(AZ_CRC_CE("o3dimportEditorService"));
    }

    void o3dimportEditorSystemComponent::GetIncompatibleServices(AZ::ComponentDescriptor::DependencyArrayType& incompatible)
    {
        incompatible.push_back(AZ_CRC_CE("o3dimportEditorService"));
    }

    void o3dimportEditorSystemComponent::GetRequiredServices([[maybe_unused]] AZ::ComponentDescriptor::DependencyArrayType& required)
    {
    }

    void o3dimportEditorSystemComponent::GetDependentServices([[maybe_unused]] AZ::ComponentDescriptor::DependencyArrayType& dependent)
    {
    }

    void o3dimportEditorSystemComponent::Activate()
    {
        o3dimportRequestBus::Handler::BusConnect();
    }

    void o3dimportEditorSystemComponent::Deactivate()
    {
        o3dimportRequestBus::Handler::BusDisconnect();
    }

} // namespace o3dimport
