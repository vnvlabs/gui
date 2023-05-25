import URI from '@theia/core/lib/common/uri';
import { injectable, inject } from '@theia/core/shared/inversify';
import { FrontendApplicationContribution, FrontendApplication } from '@theia/core/lib/browser';
import { FrontendApplicationStateService } from '@theia/core/lib/browser/frontend-application-state';
import { EditorManager } from '@theia/editor/lib/browser';
import { ApplicationShell } from '@theia/core/lib/browser';
import { Breadcrumb, BreadcrumbsService } from '@theia/core/lib/browser';

import {SplitPanel, Layout} from '@phosphor/widgets';

const MAIN_AREA_CLASS = 'theia-app-main';
/** The class name added to the bottom area panel. */
const BOTTOM_AREA_CLASS = 'theia-app-bottom';
const MAIN_AREA_ID = 'theia-main-content-panel';

@injectable()
export class CustomApplicationShell extends ApplicationShell {

    @inject(FrontendApplicationStateService)
    protected readonly stateService: FrontendApplicationStateService;
    
    protected createLayout(): Layout {
       
	const urlObj = new URL(window.location.href);
        const params = urlObj.searchParams;
        const param = params.get("shell")
	if (param != null) {

        	const leftRightSplitLayout = this.createSplitLayout(
            		[this.mainPanel, this.rightPanelHandler.container],
            		[1, 0],
            		{ orientation: 'horizontal', spacing: 0 }
        	);
        
		const panelForSideAreas = new SplitPanel({ layout: leftRightSplitLayout });
        	panelForSideAreas.id = 'theia-left-right-split-panel';

        	return this.createBoxLayout(
            		[panelForSideAreas],
            		[1],
            		{ direction: 'top-to-bottom', spacing: 0 }
        	);
        } else {
	       return super.createLayout();	
        }
    }

    protected createMainPanel() {

const urlObj = new URL(window.location.href);
        const params = urlObj.searchParams;
        const param = params.get("shell")
	if (param != null) {
        const renderer = this.dockPanelRendererFactory();
        renderer.tabBarClasses.push(BOTTOM_AREA_CLASS);
        renderer.tabBarClasses.push(MAIN_AREA_CLASS);
        const dockPanel = this.dockPanelFactory({
            mode: 'single-document',
            renderer,
            spacing: 0
        });
        dockPanel.id = MAIN_AREA_ID;

        return dockPanel;
	}
	return super.createMainPanel();
    }


}

@injectable()
export class BreadcrumbsFilterService extends BreadcrumbsService {

    async getBreadcrumbs(uri: URI): Promise<Breadcrumb[]> {
        // Skip '.json' files.
	const urlObj = new URL(window.location.href);
        const params = urlObj.searchParams;
        const param = params.get("shell")
	if (param != null) {
           return []
	}
	return super.getBreadcrumbs(uri)
    }

}



@injectable()
export class FileLoadContribution implements FrontendApplicationContribution {

    @inject(FrontendApplicationStateService)
    protected readonly stateService: FrontendApplicationStateService;

    @inject(EditorManager)
    protected readonly editorManager: EditorManager;

    async onStart(app: FrontendApplication): Promise<void> {
	   const urlObj = new URL(window.location.href);

  	   const params = urlObj.searchParams;
           const param = params.get("file")
    	   if (param != null) {
	   	this.editorManager.open(new URI(param)).then((editor)=>{
		   
			const reader = params.get("reader")
			alert(reader)
			if (reader) editor.editor.setLanguage(reader)
	        })
	   }
	   return
    }
}


