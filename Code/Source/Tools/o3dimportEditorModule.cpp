
#include <o3dimport/o3dimportTypeIds.h>
#include <o3dimportModuleInterface.h>
#include "o3dimportEditorSystemComponent.h"
#include <AzToolsFramework/API/PythonLoader.h>

#include <QtGlobal>

void Inito3dimportResources()
{
    // We must register our Qt resources (.qrc file) since this is being loaded from a separate module (gem)
    Q_INIT_RESOURCE(o3dimport);
}

namespace o3dimport
{
    class o3dimportEditorModule
        : public o3dimportModuleInterface
        , public AzToolsFramework::EmbeddedPython::PythonLoader
    {
    public:
        AZ_RTTI(o3dimportEditorModule, o3dimportEditorModuleTypeId, o3dimportModuleInterface);
        AZ_CLASS_ALLOCATOR(o3dimportEditorModule, AZ::SystemAllocator);

        o3dimportEditorModule()
        {
            Inito3dimportResources();

            // Push results of [MyComponent]::CreateDescriptor() into m_descriptors here.
            // Add ALL components descriptors associated with this gem to m_descriptors.
            // This will associate the AzTypeInfo information for the components with the the SerializeContext, BehaviorContext and EditContext.
            // This happens through the [MyComponent]::Reflect() function.
            m_descriptors.insert(m_descriptors.end(), {
                o3dimportEditorSystemComponent::CreateDescriptor(),
            });
        }

        /**
         * Add required SystemComponents to the SystemEntity.
         * Non-SystemComponents should not be added here
         */
        AZ::ComponentTypeList GetRequiredSystemComponents() const override
        {
            return AZ::ComponentTypeList {
                azrtti_typeid<o3dimportEditorSystemComponent>(),
            };
        }
    };
}// namespace o3dimport

#if defined(O3DE_GEM_NAME)
AZ_DECLARE_MODULE_CLASS(AZ_JOIN(Gem_, O3DE_GEM_NAME, _Editor), o3dimport::o3dimportEditorModule)
#else
AZ_DECLARE_MODULE_CLASS(Gem_o3dimport_Editor, o3dimport::o3dimportEditorModule)
#endif
