
#pragma once
#include <AzCore/Component/Component.h>
#include <o3dimport/o3dimportBus.h>


namespace o3dimport
{
    /// System component for o3dimport editor
    class o3dimportEditorSystemComponent
        : public o3dimportRequestBus::Handler
        , public AZ::Component
    {
    public:
        AZ_COMPONENT_DECL(o3dimportEditorSystemComponent);

        static void Reflect(AZ::ReflectContext* context);

        o3dimportEditorSystemComponent();
        ~o3dimportEditorSystemComponent();

    private:
        static void GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided);
        static void GetIncompatibleServices(AZ::ComponentDescriptor::DependencyArrayType& incompatible);
        static void GetRequiredServices(AZ::ComponentDescriptor::DependencyArrayType& required);
        static void GetDependentServices(AZ::ComponentDescriptor::DependencyArrayType& dependent);

        // AZ::Component
        void Activate() override;
        void Deactivate() override;
    };
} // namespace o3dimport
